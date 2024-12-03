"""Primary class for converting experiment-specific behavioral video."""
from pynwb.file import NWBFile
from pydantic import FilePath

from neuroconv.utils import DeepDict, dict_deep_update
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import VideoInterface


class Olson2024VideoInterface(BaseDataInterface):
    """Video interface for olson_2024 conversion"""

    keywords = ("movie", "natural behavior", "tracking")

    def __init__(self, file_paths: list[FilePath]):
        # file_paths must be sorted in the order that the videos were recorded
        assert len(file_paths) > 0, "At least one file path must be provided."
        video_interfaces = []
        for file_path in file_paths:
            metadata_key_name = (
                "Video" + file_path.parent.name
            )  # TODO: Document this naming convention in the docstring
            video_interfaces.append(VideoInterface(file_paths=[file_path], metadata_key_name=metadata_key_name))
        self.video_interfaces = video_interfaces

    def get_metadata_schema(self) -> DeepDict:
        metadata_schema = super().get_metadata_schema()
        for video_interface in self.video_interfaces:
            metadata_schema = dict_deep_update(metadata_schema, video_interface.get_metadata_schema())
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        for video_interface in self.video_interfaces:
            video_interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)
