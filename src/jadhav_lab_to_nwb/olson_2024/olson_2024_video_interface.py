"""Primary class for converting experiment-specific behavioral video."""
from pynwb.file import NWBFile
from pydantic import FilePath

from neuroconv.utils import DeepDict, dict_deep_update
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import VideoInterface

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
            metadata_key_name = "Video" + "_" + epoch_name  # TODO: Document this naming convention in the docstring
            video_interface = VideoInterface(file_paths=[file_path], metadata_key_name=metadata_key_name)
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
        for video_interface in self.video_interfaces:
            metadata_schema = dict_deep_update(metadata_schema, video_interface.get_metadata_schema())
        metadata_schema["properties"]["Behavior"]["properties"]["Video_description"] = {"type": "string"}
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        for video_interface in self.video_interfaces:
            metadata["Behavior"][video_interface.metadata_key_name][0]["description"] = metadata["Behavior"][
                "Video_description"
            ]
            video_interface.add_to_nwbfile(
                nwbfile=nwbfile, metadata=metadata, module_name="behavior"
            )  # TODO: move video back to acquisition once https://github.com/LorenFrankLab/spyglass/issues/396 is fixed.
