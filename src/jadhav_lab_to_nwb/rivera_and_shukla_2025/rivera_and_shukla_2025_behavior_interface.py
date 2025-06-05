"""Behavior interface for Rivera and Shukla 2025 dataset conversion.

This module provides the interface for converting behavioral event data from the
Rivera and Shukla 2025 experiment to NWB format. It handles the parsing of behavioral
event files and temporal alignment with other experimental data streams.
"""
from pynwb.file import NWBFile
from pynwb.behavior import BehavioralEvents
from pynwb import TimeSeries
from pydantic import FilePath
import numpy as np
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools import nwb_helpers
from neuroconv.utils import get_base_schema


class RiveraAndShukla2025BehaviorInterface(BaseDataInterface):
    """Behavior interface for Rivera and Shukla 2025 dataset conversion.

    This interface handles the conversion of behavioral event data from text files
    containing timestamped behavioral events. It processes poke events, reward
    delivery, and other behavioral markers, applying temporal alignment and clock
    rate corrections for integration with other experimental data streams.

    The interface supports multiple behavioral event files per session and handles
    the parsing of experiment-specific event formats including reward detection
    logic and temporal synchronization.
    """

    keywords = ("behavior",)

    def __init__(self, file_paths: list[FilePath]):
        """Initialize the Rivera and Shukla 2025 behavior interface.

        Sets up the interface for processing behavioral event files from the
        Rivera and Shukla 2025 dataset. Initializes temporal alignment parameters
        that can be set later for synchronization with other data streams.

        Parameters
        ----------
        file_paths : list[FilePath]
            List of paths to behavioral event text files. Each file contains
            timestamped behavioral events in the format "timestamp event_id".
            Files should be sorted in chronological order of recording.
        """
        super().__init__(file_paths=file_paths)
        self.epoch_starting_time_shifts = None
        self.clock_rates = None

    def get_metadata_schema(self):
        """Get metadata schema for behavioral event validation.

        Extends the base metadata schema to include validation rules for
        behavioral events and processing modules specific to the Rivera and
        Shukla 2025 dataset format.

        Returns
        -------
        dict
            Metadata schema dictionary with behavioral event validation rules.
        """
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Behavior"] = get_base_schema(tag="Behavior")
        metadata_schema["properties"]["Behavior"]["properties"]["Module"] = {
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
        }
        metadata_schema["properties"]["Behavior"]["properties"]["Events"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "ids": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        """Add behavioral event data to NWB file.

        Processes behavioral event files and adds timestamped behavioral events
        to the NWB file. This method handles file parsing, temporal alignment,
        clock rate corrections, and reward detection logic specific to the
        Rivera and Shukla 2025 dataset.

        Parameters
        ----------
        nwbfile : NWBFile
            The NWB file object to add behavioral data to.
        metadata : dict
            Metadata dictionary containing behavioral event definitions,
            module configuration, and event descriptions.
        """
        file_paths = self.source_data["file_paths"]
        clock_rates = self.get_clock_rates()
        epoch_starting_time_shifts = self.get_epoch_starting_time_shifts()
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name=metadata["Behavior"]["Module"]["name"],
            description=metadata["Behavior"]["Module"]["description"],
        )
        behavioral_events = BehavioralEvents(name="behavioral_events")
        event_id_to_timestamps = {}
        for file_path, clock_rate, starting_time_shift in zip(file_paths, clock_rates, epoch_starting_time_shifts):
            import os

            if file_path.name.startswith("._"):
                os.remove(file_path)
                continue
            with open(file_path, "r") as file:
                lines = file.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith("#") or line == "~~~":
                    continue  # skip comments
                timestamp, event_id = line.split(" ", 1)
                timestamp = float(timestamp) / clock_rate + starting_time_shift
                if event_id in event_id_to_timestamps:
                    event_id_to_timestamps[event_id].append(timestamp)
                else:
                    event_id_to_timestamps[event_id] = [timestamp]

                # Check if matched poke resulted in a reward
                if i + 1 == len(lines):
                    continue
                next_event_id = lines[i + 1].strip().split(" ", 1)[-1]
                if "Matched" in event_id and next_event_id != "but, no reward":
                    event_id = "rewarded_poke"
                    if event_id in event_id_to_timestamps:
                        event_id_to_timestamps[event_id].append(timestamp)
                    else:
                        event_id_to_timestamps[event_id] = [timestamp]

        for event_metadata in metadata["Behavior"]["Events"]:
            event_ids = event_metadata["ids"]
            timestamps = []
            for event_id in event_ids:
                if event_id in event_id_to_timestamps:
                    timestamps.extend(event_id_to_timestamps[event_id])
            timestamps = sorted(timestamps)
            if len(timestamps) == 0:
                continue  # If no timestamps were found for this event, skip it
            time_series = TimeSeries(
                name=event_metadata["name"],
                description=event_metadata["description"],
                data=np.ones((len(timestamps), 1)),
                timestamps=timestamps,
                unit="n.a.",
            )
            behavioral_events.add_timeseries(time_series)

        # Add reward events manually
        if "rewarded_poke" in event_id_to_timestamps:
            reward_timestamps = sorted(event_id_to_timestamps["rewarded_poke"])
            time_series = TimeSeries(
                name="rewarded_poke",
                description="Whenever a matched poke resulted in a reward.",
                data=np.ones((len(reward_timestamps), 1)),
                timestamps=reward_timestamps,
                unit="n.a.",
            )
            behavioral_events.add_timeseries(time_series)

        behavior_module.add(behavioral_events)

    def set_epoch_starting_time_shifts(self, starting_time_shifts: list[float]):
        """Set temporal shifts for epoch alignment.

        Sets the starting time shifts for each behavioral event file to align
        epochs with other data streams in the session.

        Parameters
        ----------
        starting_time_shifts : list[float]
            List of time shifts in seconds to apply to each behavioral event file.
            Must match the number of behavioral event files.
        """
        self.epoch_starting_time_shifts = starting_time_shifts

    def get_epoch_starting_time_shifts(self) -> list[float]:
        """Get temporal shifts for epoch alignment.

        Returns the starting time shifts for each behavioral event file.
        If not previously set, defaults to zero shifts for all files.

        Returns
        -------
        list[float]
            List of time shifts in seconds for each behavioral event file.
        """
        if self.epoch_starting_time_shifts is None:
            self.epoch_starting_time_shifts = [0.0] * len(self.source_data["file_paths"])
        return self.epoch_starting_time_shifts

    def set_clock_rates(self, clock_rates: list[float]):
        """Set clock rates for timestamp conversion.

        Sets the clock rates for each behavioral event file to convert integer
        timestamps to seconds. The clock rate represents the rate at which
        video frames are acquired (frames per second).

        Parameters
        ----------
        clock_rates : list[float]
            List of clock rates (frames per second) for each behavioral event file.
            Timestamps are divided by these rates to convert from frame numbers
            to seconds. Must match the number of behavioral event files.
        """
        self.clock_rates = clock_rates

    def get_clock_rates(self) -> list[float]:
        """Get clock rates for timestamp conversion.

        Returns the clock rates (frames per second) for each behavioral event file.
        If not previously set, defaults to 1.0 for all files.

        Returns
        -------
        list[float]
            List of clock rates (frames per second) for each behavioral event file.
        """
        if self.clock_rates is None:
            self.clock_rates = [1.0] * len(self.source_data["file_paths"])
        return self.clock_rates
