"""Behavior interface for Olson 2024 dataset conversion.

This module provides the behavior data interface for converting behavioral event data
from the Olson 2024 electrophysiology dataset. It handles extraction of behavioral
events from Trodes-format data files and converts them to NWB TimeSeries format.
"""
from pynwb.file import NWBFile
from pydantic import DirectoryPath
import numpy as np
from pathlib import Path

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools import nwb_helpers
from neuroconv.utils import get_base_schema

from pynwb.behavior import BehavioralEvents
from pynwb import TimeSeries

from ..tools.spikegadgets import readTrodesExtractedDataFile


class Olson2024BehaviorInterface(BaseDataInterface):
    """Data interface for converting Olson 2024 behavioral event data to NWB format.

    This interface handles behavioral event data from electrophysiology experiments,
    extracting event timestamps from Trodes-format .dat files and converting them
    to NWB TimeSeries within a BehavioralEvents container.
    """

    keywords = ("behavior",)

    def __init__(self, folder_path: DirectoryPath):
        """Initialize the Olson 2024 behavior interface.

        Parameters
        ----------
        folder_path : DirectoryPath
            Path to directory containing Trodes-format behavioral event files (.dat).
            Each .dat file should contain event timestamps and metadata for a specific
            behavioral event type (e.g., reward delivery, lever presses).
        """
        super().__init__(folder_path=folder_path)

    def get_metadata_schema(self):
        """Get metadata schema for behavioral events.

        Returns
        -------
        dict
            Schema dictionary defining the structure for behavioral event metadata.
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
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        """Add behavioral event data to the NWB file.

        Reads Trodes-format .dat files, extracts event timestamps, and adds them
        as TimeSeries objects within a BehavioralEvents container in the NWB file.

        Parameters
        ----------
        nwbfile : NWBFile
            The NWB file object to add behavioral data to.
        metadata : dict
            Metadata dictionary containing behavioral event descriptions and module info.
        """
        folder_path = Path(self.source_data["folder_path"])
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name=metadata["Behavior"]["Module"]["name"],
            description=metadata["Behavior"]["Module"]["description"],
        )
        behavioral_events = BehavioralEvents(name="behavioral_events")
        for file_path in folder_path.glob(r"*.dat"):
            fieldsText = readTrodesExtractedDataFile(file_path)
            rate = np.asarray(fieldsText["clockrate"], dtype="float64")
            timestamps = fieldsText["data"]["time"][fieldsText["data"]["state"] == 1]
            timestamps = np.asarray(timestamps, dtype="float64") / rate
            event_id = fieldsText["id"]
            event_metadata = next(
                event_metadata for event_metadata in metadata["Behavior"]["Events"] if event_metadata["id"] == event_id
            )
            if len(timestamps) == 0:
                continue
            time_series = TimeSeries(
                name=event_metadata["name"],
                description=event_metadata["description"],
                data=np.ones((len(timestamps), 1)),
                timestamps=timestamps,
                unit="n.a.",
                continuity="instantaneous",
            )
            behavioral_events.add_timeseries(time_series)
        behavior_module.add(behavioral_events)
