"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pydantic import DirectoryPath
import numpy as np

from neuroconv.basedatainterface import BaseDataInterface
from .tools.spikegadgets import readCameraModuleTimeStamps
from .utils.utils import get_epoch_name


class Olson2024EpochInterface(BaseDataInterface):
    """Epoch interface for olson_2024 conversion"""

    keywords = ("behavior",)

    def __init__(self, epoch_folder_paths: list[DirectoryPath]):
        super().__init__(epoch_folder_paths=epoch_folder_paths)

    def get_metadata_schema(self):
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Epochs"] = {
            "description": "Metadata for each epoch",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "task_name": {"type": "string"},
                    "led_configuration": {"type": "string"},
                    "led_list": {"type": "array", "items": {"type": "string"}},
                    "led_positions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "task_name", "led_configuration", "led_list", "led_positions"],
            },
        }
        metadata_schema["properties"]["Tasks"] = {
            "description": "Metadata for each task",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "camera_id": {"type": "string"},
                },
                "required": ["name", "description", "camera_id"],
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        epoch_folder_paths = self.source_data["epoch_folder_paths"]
        nwbfile.add_epoch_column(name="epoch_name", description="Full name of the epoch")
        nwbfile.add_epoch_column(name="epoch_id", description="Epoch ID")
        nwbfile.add_epoch_column(name="frag_id", description="Frag ID")  # TODO: What is a frag ID?
        nwbfile.add_epoch_column(name="env_id", description="Environment ID")
        nwbfile.add_epoch_column(name="task_id", description="Task ID")
        nwbfile.add_epoch_column(name="task_name", description="Full name of the task")
        nwbfile.add_epoch_column(name="task_description", description="Description of the task")
        nwbfile.add_epoch_column(name="camera_id", description="Camera ID")
        nwbfile.add_epoch_column(name="led_configuration", description="LED configuration")
        nwbfile.add_epoch_column(name="led_list", description="Comma-separated list of LEDs")
        nwbfile.add_epoch_column(name="led_positions", description="Comma-separated list of LED positions")
        for epoch_folder_path in epoch_folder_paths:
            epoch_name = get_epoch_name(epoch_folder_path.name)
            epoch_id, frag_id, env_id, task_id = epoch_name.split("_")
            epoch_metadata = next(meta for meta in metadata["Epochs"] if meta["name"] == epoch_id)
            task_name = epoch_metadata["task_name"]
            task_metadata = next(meta for meta in metadata["Tasks"] if meta["name"] == task_name)
            task_description = task_metadata["description"]
            camera_id = task_metadata["camera_id"]
            led_configuration = epoch_metadata["led_configuration"]
            led_list = ",".join(epoch_metadata["led_list"])
            led_positions = ",".join(epoch_metadata["led_positions"])
            video_timestamps_file_path = epoch_folder_path / f"{epoch_folder_path.name}.1.videoTimeStamps"
            timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
            start_time = timestamps[0]
            stop_time = timestamps[-1]
            nwbfile.add_epoch(
                start_time=start_time,
                stop_time=stop_time,
                epoch_name=epoch_name,
                epoch_id=epoch_id,
                frag_id=frag_id,
                env_id=env_id,
                task_id=task_id,
                task_name=task_name,
                task_description=task_description,
                camera_id=camera_id,
                led_configuration=led_configuration,
                led_list=led_list,
                led_positions=led_positions,
                tags=[epoch_name],
            )
