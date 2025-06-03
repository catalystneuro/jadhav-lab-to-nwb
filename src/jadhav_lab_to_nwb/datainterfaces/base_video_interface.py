"""Base interface for converting behavioral video data to NWB format.

This module provides the foundational interface for handling behavioral video recordings
in neuroscience experiments. It manages video file organization, camera device metadata,
and integration with temporal alignment systems for synchronizing video data with other
experimental modalities.
"""
from abc import abstractmethod
from pynwb.file import NWBFile
from pydantic import FilePath

from neuroconv.utils import DeepDict, dict_deep_update
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import ExternalVideoInterface
from neuroconv.utils import get_base_schema
from ndx_franklab_novela import CameraDevice


class BaseVideoInterface(BaseDataInterface):
    """Base interface for converting behavioral video data to NWB format.

    This abstract base class provides core functionality for handling behavioral
    video recordings in neuroscience experiments. It manages video files across
    multiple epochs and segments, handles camera device metadata, and coordinates
    temporal synchronization with other experimental data streams.

    The interface supports multi-camera setups and provides flexible video naming
    and task association through abstract methods. It integrates with the broader
    NWB conversion pipeline by managing video data organization and camera device
    registration using the ndx-franklab-novela extension.


    Notes
    -----
    This is an abstract base class that requires implementation of:
    - get_video_name: Extract video name from file names
    - get_task_name: Determine task association for videos
    """

    keywords = ("movie", "natural behavior", "tracking")

    def __init__(self, file_paths: list[FilePath | list], video_timestamps_file_paths: list[FilePath | list]):
        """Initialize the BaseVideoInterface.

        Sets up individual ExternalVideoInterface objects for each epoch and stores
        timestamp file paths for temporal alignment. The nested structure supports
        multiple epochs per session, where each epoch can contain multiple video
        segments that are handled by a single ExternalVideoInterface.

        Parameters
        ----------
        file_paths : list[FilePath | list]
            Video file paths organized by epoch. The top level corresponds to multiple
            epochs per session, and the nested level corresponds to multiple segments
            per epoch. Each epoch creates a single ExternalVideoInterface that may
            handle multiple video files (segments). Files must be sorted in the order
            that videos were recorded.
        video_timestamps_file_paths : list[FilePath | list]
            Corresponding timestamp file paths for temporal alignment. Must match
            the structure and length of file_paths. Each timestamp file provides
            temporal synchronization data for the corresponding video files.

        Raises
        ------
        AssertionError
            If file_paths is empty or if the number of file paths doesn't match
            the number of timestamp file paths.
        """
        # file_paths must be sorted in the order that the videos were recorded
        assert len(file_paths) > 0, "At least one file path must be provided."
        assert len(file_paths) == len(
            video_timestamps_file_paths
        ), "The number of file paths must match the number of video timestamps file paths."
        self.video_timestamps_file_paths = video_timestamps_file_paths

        video_interfaces = []
        for epoch_file_paths in file_paths:
            if not isinstance(epoch_file_paths, list):
                epoch_file_paths = [epoch_file_paths]
            video_name = self.get_video_name(file_name=epoch_file_paths[0].name)
            video_interface = ExternalVideoInterface(file_paths=epoch_file_paths, video_name=video_name)
            video_interfaces.append(video_interface)
        self.video_interfaces = video_interfaces
        self.starting_frames = [None] * len(self.video_interfaces)

    @abstractmethod
    def get_video_name(self, file_name: str) -> str:
        """Extract video name from file name.

        This method must be implemented by subclasses to define how video names
        are generated from video file names. The video name is used as an identifier
        in the NWB file and for linking with other data streams.

        Parameters
        ----------
        file_name : str
            Name of the video file.

        Returns
        -------
        str
            The extracted or generated video name.
        """
        pass

    def get_metadata(self) -> DeepDict:
        """Aggregate metadata from all video interfaces.

        Collects and merges metadata from all individual video interfaces
        managed by this base interface. This includes video file information,
        timestamps, and device configurations.

        Returns
        -------
        DeepDict
            Merged metadata dictionary containing all video metadata.
        """
        metadata = super().get_metadata()
        for video_interface in self.video_interfaces:
            metadata = dict_deep_update(metadata, video_interface.get_metadata())
        return metadata

    def get_metadata_schema(self) -> DeepDict:
        """Get metadata schema including video and camera device validation rules.

        Extends the base metadata schema to include validation rules for video
        metadata and camera device configurations. This ensures proper structure
        for behavioral video experiments.

        Returns
        -------
        DeepDict
            Metadata schema dictionary with video and camera validation rules.

        """
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Behavior"] = get_base_schema(tag="Behavior")
        metadata_schema["properties"]["Behavior"]["properties"]["Video"] = {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "General description of the video recording setup and purpose",
                },
                "CameraDevice": {
                    "description": "Metadata for each camera device, compatible with spyglass",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Unique identifier for the camera device. Must be formatted as 'camera_device <id>'.",
                            },
                            "meters_per_pixel": {
                                "type": "number",
                                "description": "Spatial resolution of the camera in meters per pixel",
                            },
                            "manufacturer": {"type": "string", "description": "Name of the camera manufacturer"},
                            "model": {"type": "string", "description": "Model number or name of the camera"},
                            "lens": {"type": "string", "description": "Specifications of the camera lens"},
                            "camera_name": {
                                "type": "string",
                                "description": "Common name or label used for the camera",
                            },
                        },
                        "required": ["name", "meters_per_pixel", "manufacturer", "model", "lens", "camera_name"],
                    },
                },
            },
            "required": ["description", "CameraDevice"],
        }
        for video_interface in self.video_interfaces:
            metadata_schema = dict_deep_update(metadata_schema, video_interface.get_metadata_schema())
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        """Add video data and camera devices to NWB file.

        This method performs several operations:
        1. Creates and registers camera devices from metadata
        2. Links video interfaces with appropriate camera devices
        3. Adds video data to the NWB file with proper device associations

        For each video interface, determines the associated task and camera,
        then updates metadata to establish proper device linkages before
        adding the video data to the NWB file.

        Parameters
        ----------
        nwbfile : NWBFile
            The NWB file object to add video data to.
        metadata : dict
            Metadata dictionary containing video, camera, and task information.
            Must include 'Behavior', 'Tasks', and camera device configurations.

        Notes
        -----
        Camera devices are created using the ndx-franklab-novela extension
        and include spatial calibration information for behavioral analysis.
        """
        for camera_device_metadata in metadata["Behavior"]["Video"]["CameraDevice"]:
            camera_device = CameraDevice(
                name=camera_device_metadata["name"],
                meters_per_pixel=camera_device_metadata["meters_per_pixel"],
                model=camera_device_metadata["model"],
                lens=camera_device_metadata["lens"],
                camera_name=camera_device_metadata["camera_name"],
            )
            nwbfile.add_device(camera_device)
        video_description = metadata["Behavior"]["Video"]["description"]
        for video_interface, starting_frames in zip(self.video_interfaces, self.starting_frames):
            task_name = self.get_task_name(metadata, video_interface.video_name)
            task_metadata = next(meta for meta in metadata["Tasks"] if meta["name"] == task_name)
            camera_id = task_metadata["camera_id"][0]
            device_name = f"camera_device {camera_id}"
            metadata["Behavior"]["ExternalVideos"][video_interface.video_name]["device"] = dict(name=device_name)
            metadata["Behavior"]["ExternalVideos"][video_interface.video_name]["description"] = video_description
            video_interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, starting_frames=starting_frames)

    @abstractmethod
    def get_task_name(self, metadata: dict, video_name: str) -> str:
        """Determine task name associated with a video.

        This method must be implemented by subclasses to define how task names
        are determined from video names and metadata. This is used to link
        video data with corresponding behavioral tasks and camera configurations.

        Parameters
        ----------
        metadata : dict
            Metadata dictionary containing task information.
        video_name : str
            Name of the video to find task association for.

        Returns
        -------
        str
            The task name associated with this video.
        """
        pass

    def set_starting_frames(self, starting_frames: list[list[int]]):
        """Set the starting frames for each video interface.

        This method allows setting custom starting frame indices for video
        synchronization. This is useful when videos need to be aligned or
        when only a portion of the video should be included in the NWB file.

        Parameters
        ----------
        starting_frames : list[list[int]]
            List of starting frame indices for each video interface.
            Must match the number of video interfaces.

        Raises
        ------
        AssertionError
            If the number of starting frames doesn't match the number of
            video interfaces.
        """
        assert len(starting_frames) == len(
            self.video_interfaces
        ), "The number of starting frames must match the number of video interfaces."
        self.starting_frames = starting_frames
