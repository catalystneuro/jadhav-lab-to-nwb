"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pynwb.core import DynamicTable
from pydantic import DirectoryPath
import numpy as np

from neuroconv.basedatainterface import BaseDataInterface
from ..common.tools.spikegadgets import readCameraModuleTimeStamps
from ..common.utils.utils import olson_2024_get_epoch_name


class Olson2024EpochInterface(BaseDataInterface):
    """Epoch interface for olson_2024 conversion"""

    keywords = ("behavior",)

    def __init__(self, epoch_folder_paths: list[DirectoryPath]):
        super().__init__(epoch_folder_paths=epoch_folder_paths)

    def get_metadata_schema(self):
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Tasks"] = {
            "description": "Metadata for each task",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "environment": {"type": "string"},
                    "camera_id": {"type": "array", "items": {"type": "integer"}},
                    "led_configuration": {"type": "string"},
                    "led_list": {"type": "array", "items": {"type": "string"}},
                    "led_positions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "description", "environment", "camera_id"],
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        epoch_folder_paths = self.source_data["epoch_folder_paths"]
        sleep_epochs, shuttle_epochs = [], []
        for epoch_folder_path in epoch_folder_paths:
            epoch_name = olson_2024_get_epoch_name(epoch_folder_path.name)
            epoch_id, _, _, _ = epoch_name.split("_")
            video_timestamps_file_path = epoch_folder_path / f"{epoch_folder_path.name}.1.videoTimeStamps"
            timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
            start_time = timestamps[0]
            stop_time = timestamps[-1]
            tag = epoch_id[1:]  # from S01 to 01
            epoch_number = int(tag)
            if "SLP" in epoch_name:
                sleep_epochs.append(epoch_number)
            elif "HomeAltVisitAll" in epoch_name:
                shuttle_epochs.append(epoch_number)
            else:
                raise ValueError(f"Unknown epoch type in {epoch_name} for epoch_folder_path {epoch_folder_path.name}")

            nwbfile.add_epoch(
                start_time=start_time,
                stop_time=stop_time,
                tags=[tag],
            )

        tasks_metadata = metadata["Tasks"]
        tasks_module = nwbfile.create_processing_module(name="tasks", description="tasks module")
        for task_metadata in tasks_metadata:
            name = task_metadata["name"]
            description = task_metadata["description"]
            environment = task_metadata["environment"]
            camera_id = task_metadata["camera_id"]
            led_configuration = task_metadata["led_configuration"]
            led_list = ",".join(task_metadata["led_list"])
            led_positions = ",".join(task_metadata["led_positions"])
            if name == "Sleep":
                task_epochs = sleep_epochs
            elif name == "HomeAltVisitAll":
                task_epochs = shuttle_epochs
            else:
                raise ValueError(
                    f"Unknown task name {name} in task_metadata {task_metadata}. Expected 'Sleep' or 'HomeAltVisitAll'."
                )
            task_table = DynamicTable(name=name, description=description)
            task_table.add_column(name="task_name", description="Name of the task.")
            task_table.add_column(name="task_description", description="Description of the task.")
            task_table.add_column(name="task_environment", description="The environment the animal was in.")
            task_table.add_column(name="camera_id", description="Camera ID.")
            task_table.add_column(name="led_configuration", description="LED configuration")
            task_table.add_column(name="led_list", description="Comma-separated list of LED names")
            task_table.add_column(name="led_positions", description="Comma-separated list of LED positions")
            task_table.add_column(name="task_epochs", description="Task epochs.")
            task_table.add_row(
                task_name=name,
                task_description=description,
                task_environment=environment,
                camera_id=camera_id,
                led_configuration=led_configuration,
                led_list=led_list,
                led_positions=led_positions,
                task_epochs=task_epochs,
            )
            tasks_module.add(task_table)
