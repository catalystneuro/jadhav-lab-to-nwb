"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pynwb.core import DynamicTable
from pydantic import DirectoryPath
import numpy as np

from neuroconv.basedatainterface import BaseDataInterface
from .tools.spikegadgets import readCameraModuleTimeStamps
from .utils.utils import get_epoch_name

from ndx_franklab_novela import CameraDevice  # TODO: move to video interface


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
                    "camera_id": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["name", "description", "camera_id"],
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # TODO: move camera info to videointerface
        camera_0 = CameraDevice(
            name="Camera 0",
            meters_per_pixel=1.0,
            model="my_model",
            lens="my_lens",
            camera_name="my_camera_name_0",
        )
        camera_1 = CameraDevice(
            name="Camera 1",
            meters_per_pixel=1.0,
            model="my_model",
            lens="my_lens",
            camera_name="my_camera_name_1",
        )
        nwbfile.add_device(camera_0)
        nwbfile.add_device(camera_1)

        tasks_metadata = metadata["Tasks"]
        tasks_module = nwbfile.create_processing_module(name="tasks", description="tasks module")
        for task_metadata in tasks_metadata:
            name = task_metadata["name"]
            description = task_metadata["description"]
            environment = task_metadata["environment"]
            camera_id = task_metadata["camera_id"]
            task_epochs = task_metadata["task_epochs"]
            task_table = DynamicTable(name=name, description=description)
            task_table.add_column(name="task_name", description="Name of the task.")
            task_table.add_column(name="task_description", description="Description of the task.")
            task_table.add_column(name="task_environment", description="The environment the animal was in.")
            task_table.add_column(name="camera_id", description="Camera ID.")
            task_table.add_column(name="task_epochs", description="Task epochs.")
            task_table.add_row(
                task_name=name,
                task_description=description,
                task_environment=environment,
                camera_id=camera_id,
                task_epochs=task_epochs,
            )
            tasks_module.add(task_table)

        epoch_folder_paths = self.source_data["epoch_folder_paths"]
        nwbfile.add_epoch_column(name="frag_id", description="Frag ID")  # TODO: What is a frag ID?
        nwbfile.add_epoch_column(name="led_configuration", description="LED configuration")
        nwbfile.add_epoch_column(name="led_list", description="List of LED names")
        nwbfile.add_epoch_column(name="led_positions", description="List of LED positions")
        for epoch_folder_path in epoch_folder_paths:
            epoch_name = get_epoch_name(epoch_folder_path.name)
            epoch_id, frag_id, _, _ = epoch_name.split("_")
            epoch_metadata = next(meta for meta in metadata["Epochs"] if meta["name"] == epoch_id)
            task_name = epoch_metadata["task_name"]
            task_metadata = next(meta for meta in metadata["Tasks"] if meta["name"] == task_name)
            led_configuration = epoch_metadata["led_configuration"]
            led_list = epoch_metadata["led_list"]
            led_positions = epoch_metadata["led_positions"]
            video_timestamps_file_path = epoch_folder_path / f"{epoch_folder_path.name}.1.videoTimeStamps"
            timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
            start_time = timestamps[0]
            stop_time = timestamps[-1]
            tag = epoch_id[1:]  # from S01 to 01
            nwbfile.add_epoch(
                start_time=start_time,
                stop_time=stop_time,
                frag_id=frag_id,
                led_configuration=led_configuration,
                led_list=led_list,
                led_positions=led_positions,
                tags=[tag],
            )
