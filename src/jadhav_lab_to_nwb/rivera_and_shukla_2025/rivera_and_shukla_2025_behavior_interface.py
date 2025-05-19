"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pynwb.behavior import BehavioralEvents
from pynwb import TimeSeries
from pydantic import FilePath
import numpy as np
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools import nwb_helpers
from neuroconv.utils import get_base_schema


class RiveraAndShukla2025BehaviorInterface(BaseDataInterface):
    """Behavior interface for rivera_and_shukla_2025 conversion"""

    keywords = ("behavior",)

    def __init__(self, file_paths: list[FilePath], clock_rates: list[float]):
        super().__init__(file_paths=file_paths, clock_rates=clock_rates)

    def get_metadata_schema(self):
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
        file_paths = self.source_data["file_paths"]
        clock_rates = self.source_data["clock_rates"]
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name=metadata["Behavior"]["Module"]["name"],
            description=metadata["Behavior"]["Module"]["description"],
        )
        behavioral_events = BehavioralEvents(name="behavioral_events")
        event_id_to_timestamps = {}
        for file_path, clock_rate in zip(file_paths, clock_rates):
            with open(file_path, "r") as file:
                lines = file.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith("#"):
                    continue  # skip comments
                timestamp, event_id = line.split(" ", 1)
                timestamp = float(timestamp) / clock_rate
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
