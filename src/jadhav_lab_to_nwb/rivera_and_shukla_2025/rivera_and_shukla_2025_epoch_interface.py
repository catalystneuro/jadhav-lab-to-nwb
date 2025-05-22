"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from pynwb.core import DynamicTable
from pydantic import DirectoryPath
import numpy as np

from neuroconv.basedatainterface import BaseDataInterface
from ..olson_2024.tools.spikegadgets import readCameraModuleTimeStamps
from .utils.utils import get_epoch_name


class RiveraAndShukla2025EpochInterface(BaseDataInterface):
    """Epoch interface for rivera_and_shukla_2025 conversion"""

    keywords = ("behavior",)

    def __init__(self, video_timestamps_file_paths: list[DirectoryPath]):
        super().__init__(video_timestamps_file_paths=video_timestamps_file_paths)

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
        video_timestamps_file_paths = self.source_data["video_timestamps_file_paths"]
        subject_id = metadata["Subject"]["subject_id"]
        left_epochs, right_epochs = [], []
        for video_timestamps_file_path in video_timestamps_file_paths:
            epoch_name = get_epoch_name(video_timestamps_file_path.name)
            epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
            timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
            start_time = timestamps[0]
            stop_time = timestamps[-1]
            tag = f"{int(epoch_number):02d}"  # Spyglass requires 2-digit string epoch numbers
            nwbfile.add_epoch(
                start_time=start_time,
                stop_time=stop_time,
                tags=[tag],
            )
            if subject_id == subject_id1:
                left_epochs.append(epoch_number)
            elif subject_id == subject_id2:
                right_epochs.append(epoch_number)

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
            task_epochs = left_epochs if name == "SocialW_Left" else right_epochs
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
