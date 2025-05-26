"""Primary class for converting experiment-specific behavior."""
from abc import abstractmethod
from pynwb.file import NWBFile
from pynwb.core import DynamicTable
from pydantic import DirectoryPath
import numpy as np
from copy import deepcopy


from ..common.tools.spikegadgets import readCameraModuleTimeStamps
from neuroconv.basetemporalalignmentinterface import BaseTemporalAlignmentInterface


class BaseEpochInterface(BaseTemporalAlignmentInterface):
    """Epoch interface for rivera_and_shukla_2025 conversion"""

    keywords = ("behavior",)

    def __init__(self, video_timestamps_file_paths: list[DirectoryPath]):
        super().__init__(video_timestamps_file_paths=video_timestamps_file_paths)
        self.timestamps = None

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
        metadata = deepcopy(metadata)
        self.add_epochs_to_nwbfile(
            nwbfile=nwbfile,
            metadata=metadata,
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
            task_epochs = task_metadata["task_epochs"]
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

    @abstractmethod
    def add_epochs_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: dict,
    ):
        pass

    def get_original_timestamps(self) -> list[np.ndarray]:
        """Get the original timestamps for the video files."""
        video_timestamps_file_paths = self.source_data["video_timestamps_file_paths"]
        original_timestamps = []
        for video_timestamps_file_path in video_timestamps_file_paths:
            timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
            original_timestamps.append(timestamps)
        return original_timestamps

    def get_timestamps(self) -> list[np.ndarray]:
        return self.timestamps if self.timestamps is not None else self.get_original_timestamps()

    def set_aligned_timestamps(self, aligned_timestamps: list[np.ndarray]):
        self.timestamps = aligned_timestamps
