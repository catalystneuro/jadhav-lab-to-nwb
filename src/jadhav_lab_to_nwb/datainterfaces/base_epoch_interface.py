"""Base interface for converting behavioral epoch data to NWB format.

This module provides the foundational interface for handling behavioral epoch data
in neuroscience experiments. It manages temporal alignment of behavioral events
with video timestamps and organizes task-specific metadata within the NWB file structure.
"""
from abc import abstractmethod
from pynwb.file import NWBFile
from pynwb.core import DynamicTable
from pydantic import FilePath
import numpy as np
from copy import deepcopy


from ..tools.spikegadgets import readCameraModuleTimeStamps
from neuroconv.basetemporalalignmentinterface import BaseTemporalAlignmentInterface


class BaseEpochInterface(BaseTemporalAlignmentInterface):
    """Base interface for converting behavioral epoch data to NWB format.

    This abstract base class provides core functionality for handling behavioral
    epoch data in neuroscience experiments. It manages the temporal alignment of
    behavioral events with video timestamps across multiple epochs and segments, and organizes task-specific metadata
    within the NWB file structure.

    The interface supports multiple experimental tasks with associated video
    recordings, LED configurations, and environmental contexts. It integrates
    with the broader NWB conversion pipeline through temporal alignment and
    structured metadata organization.

    Notes
    -----
    This is an abstract base class that requires implementation of:
    - add_epochs_to_nwbfile: Add epoch-specific data to NWB file
    """

    keywords = ("behavior",)

    def __init__(self, video_timestamps_file_paths: list[FilePath | list[FilePath]]):
        """Initialize the BaseEpochInterface.

        Sets up the interface for temporal alignment using video timestamp files.
        The nested structure supports multiple epochs per session, where each epoch
        can contain multiple video segments. The timestamps attribute is initialized
        as None and will be set during the temporal alignment process.

        Parameters
        ----------
        video_timestamps_file_paths : list[FilePath | list[FilePath]]
            Video timestamp file paths organized by epoch. The top level corresponds
            to multiple epochs per session, and the nested level corresponds to
            multiple segments per epoch. Each timestamp file provides temporal
            synchronization data for aligning behavioral events with video recordings.
            Files must be sorted in the order that videos were recorded.
        """
        super().__init__(video_timestamps_file_paths=video_timestamps_file_paths)
        self.timestamps = None

    def get_metadata_schema(self):
        """Get metadata schema including task-specific validation rules.

        Extends the base metadata schema to include validation rules for
        task metadata. This ensures that task information conforms to the
        expected structure for behavioral experiments.

        Returns
        -------
        dict
            Metadata schema dictionary with task validation rules.
        """
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
        """Add behavioral epoch data and task metadata to NWB file.

        This method performs two main operations:
        1. Calls the abstract add_epochs_to_nwbfile method to add epoch-specific data
        2. Creates a tasks processing module with structured task metadata tables

        For each task in the metadata, creates a DynamicTable containing:
        - Task identification (name, description)
        - Environmental context
        - Camera and LED configurations
        - Associated epoch information

        Parameters
        ----------
        nwbfile : NWBFile
            The NWB file object to add behavioral data to.
        metadata : dict
            Metadata dictionary containing task information and configurations.
            Must include a 'Tasks' key with task-specific metadata.

        Notes
        -----
        Tasks with no associated epochs are skipped to avoid creating empty tables.
        LED information is stored as comma-separated strings for compatibility.
        """
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
            task_epochs = task_metadata.get("task_epochs", [])
            if len(task_epochs) == 0:
                continue  # Skip tasks with no epochs
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
        """Add epoch-specific data to NWB file.

        This abstract method must be implemented by subclasses to define how
        epoch data is added to the NWB file. This typically includes creating
        epoch tables with start/stop times and associated metadata.

        Parameters
        ----------
        nwbfile : NWBFile
            The NWB file object to add epoch data to.
        metadata : dict
            Metadata dictionary containing epoch information and configurations.
        """
        pass

    def get_original_timestamps(self) -> list[list[np.ndarray]]:
        """Get the original timestamps for the video files.

        Reads timestamp data from video timestamp files using the SpikeGadgets
        readCameraModuleTimeStamps function. This provides the raw temporal
        information for aligning behavioral data with video recordings.

        Returns
        -------
        list[list[np.ndarray]]
            Nested list of timestamp arrays. Outer list corresponds to epochs,
            inner list corresponds to video files within each epoch.
        """
        video_timestamps_file_paths = self.source_data["video_timestamps_file_paths"]
        original_timestamps = []
        for epoch_video_timestamps_file_paths in video_timestamps_file_paths:
            if not isinstance(epoch_video_timestamps_file_paths, list):
                epoch_video_timestamps_file_paths = [epoch_video_timestamps_file_paths]
            original_epoch_timestamps = []
            for video_timestamps_file_path in epoch_video_timestamps_file_paths:
                timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
                original_epoch_timestamps.append(timestamps)
            original_timestamps.append(original_epoch_timestamps)
        return original_timestamps

    def get_timestamps(self) -> list[list[np.ndarray]]:
        """Get timestamps for video files, using aligned timestamps if available.

        Returns aligned timestamps if they have been set during temporal alignment,
        otherwise returns the original timestamps from the video files.

        Returns
        -------
        list[list[np.ndarray]]
            Nested list of timestamp arrays. Uses aligned timestamps if available,
            otherwise falls back to original timestamps.
        """
        return self.timestamps if self.timestamps is not None else self.get_original_timestamps()

    def set_aligned_timestamps(self, aligned_timestamps: list[list[np.ndarray]]):
        """Set aligned timestamps for temporal synchronization.

        This method is called during the temporal alignment process to store
        the synchronized timestamps that align behavioral data with other
        data streams (e.g., electrophysiology, video).

        Parameters
        ----------
        aligned_timestamps : list[list[np.ndarray]]
            Nested list of aligned timestamp arrays. Outer list corresponds to epochs,
            inner list corresponds to video files within each epoch.
        """
        self.timestamps = aligned_timestamps
