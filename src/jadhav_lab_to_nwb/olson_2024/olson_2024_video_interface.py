"""Primary class for converting experiment-specific behavioral video."""
from pynwb.file import NWBFile
from pydantic import FilePath
import re

from neuroconv.utils import DeepDict, dict_deep_update
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import ExternalVideoInterface
from neuroconv.utils import get_base_schema
from ndx_franklab_novela import CameraDevice

from .tools.spikegadgets import readCameraModuleTimeStamps
from .utils.utils import get_epoch_name


class Olson2024VideoInterface(BaseDataInterface):
    """Video interface for olson_2024 conversion"""

    keywords = ("movie", "natural behavior", "tracking")

    def __init__(self, file_paths: list[FilePath], video_timestamps_file_paths: list[FilePath]):
        # file_paths must be sorted in the order that the videos were recorded
        assert len(file_paths) > 0, "At least one file path must be provided."
        assert len(file_paths) == len(
            video_timestamps_file_paths
        ), "The number of file paths must match the number of video timestamps file paths."
        video_interfaces = []
        for file_path, video_timestamps_file_path in zip(file_paths, video_timestamps_file_paths):
            epoch_name = get_epoch_name(name=file_path.parent.name)
            video_name = "Video" + "_" + epoch_name  # TODO: Document this naming convention in the docstring
            video_interface = ExternalVideoInterface(file_paths=[file_path], video_name=video_name)
            timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
            video_interface.set_aligned_timestamps(aligned_timestamps=[timestamps])
            video_interfaces.append(video_interface)
        self.video_interfaces = video_interfaces

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        for video_interface in self.video_interfaces:
            metadata = dict_deep_update(metadata, video_interface.get_metadata())
        return metadata

    def get_metadata_schema(self) -> DeepDict:
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
        for video_interface in self.video_interfaces:
            session_id = re.search("S[0-9][0-9]", video_interface.video_name).group(0)
            task_epoch = int(session_id[1:])
            task_metadata = next(meta for meta in metadata["Tasks"] if task_epoch in meta["task_epochs"])
            camera_id = task_metadata["camera_id"][0]
            device_name = f"camera_device {camera_id}"
            metadata["Behavior"]["ExternalVideos"][video_interface.video_name]["device"] = dict(name=device_name)
            metadata["Behavior"]["ExternalVideos"][video_interface.video_name]["description"] = video_description
            video_interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)
