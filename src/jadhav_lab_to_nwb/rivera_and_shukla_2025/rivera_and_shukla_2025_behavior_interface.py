"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pydantic import FilePath
import numpy as np
from pathlib import Path

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools import nwb_helpers
from neuroconv.utils import get_base_schema

from pynwb.behavior import BehavioralEvents
from pynwb import TimeSeries

from ..olson_2024.tools.spikegadgets import readTrodesExtractedDataFile


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
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
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
            for line in lines:
                line = line.strip()
                if line.startswith("#"):
                    continue  # skip comments
                timestamp, event_id = line.split(" ", 1)
                timestamp = float(timestamp) / clock_rate
                if event_id in event_id_to_timestamps:
                    event_id_to_timestamps[event_id].append(timestamp)
                else:
                    event_id_to_timestamps[event_id] = [timestamp]

        for event_id, timestamps in event_id_to_timestamps.items():
            event_id_is_in_metadata = False
            for event_metadata in metadata["Behavior"]["Events"]:
                if event_metadata["id"] == event_id:
                    event_id_is_in_metadata = True
                    break
            if not event_id_is_in_metadata:
                continue  # If the event ID is not in the metadata, skip it
            time_series = TimeSeries(
                name=event_metadata["name"],
                description=event_metadata["description"],
                data=np.ones((len(timestamps), 1)),
                timestamps=timestamps,
                unit="n.a.",
            )
            behavioral_events.add_timeseries(time_series)
        behavior_module.add(behavioral_events)
