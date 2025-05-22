"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pydantic import DirectoryPath
import numpy as np
from pathlib import Path

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools import nwb_helpers
from neuroconv.utils import get_base_schema

from pynwb.behavior import BehavioralEvents
from pynwb import TimeSeries

from ..common.tools.spikegadgets import readTrodesExtractedDataFile


class Olson2024BehaviorInterface(BaseDataInterface):
    """Behavior interface for olson_2024 conversion"""

    keywords = ("behavior",)

    def __init__(self, folder_path: DirectoryPath):
        super().__init__(folder_path=folder_path)

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
            time_series = TimeSeries(
                name=event_metadata["name"],
                description=event_metadata["description"],
                data=np.ones((len(timestamps), 1)),
                timestamps=timestamps,
                unit="n.a.",
            )
            behavioral_events.add_timeseries(time_series)
        behavior_module.add(behavioral_events)
