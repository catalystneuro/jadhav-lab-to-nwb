"""Primary class for converting experiment-specific behavioral video."""
from pynwb.file import NWBFile
from pydantic import FilePath
from typing import Optional

from neuroconv.utils import DeepDict, dict_deep_update
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import DeepLabCutInterface

from .utils.utils import get_epoch_name


class Olson2024DeepLabCutInterface(BaseDataInterface):
    """DeepLabCut interface for olson_2024 conversion"""

    keywords = ("DLC",)

    def __init__(
        self,
        file_paths: list[FilePath],
        config_file_paths: Optional[list[FilePath]] = None,
        subject_name: str = "ind1",
        verbose: bool = True,
    ):
        # file_paths must be sorted in the order that the videos were recorded
        assert len(file_paths) > 0, "At least one file path must be provided."
        if config_file_paths is None:
            config_file_paths = [None] * len(file_paths)
        assert len(file_paths) == len(
            config_file_paths
        ), "The number of file paths must match the number of config file paths."
        dlc_interfaces = []
        for file_path, config_file_path in zip(file_paths, config_file_paths):
            dlc_interface = DeepLabCutInterface(
                file_path=file_path,
                config_file_path=config_file_path,
                subject_name=subject_name,
                verbose=verbose,
            )
            dlc_interfaces.append(dlc_interface)
        self.dlc_interfaces = dlc_interfaces

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        for dlc_interface in self.dlc_interfaces:
            metadata = dict_deep_update(metadata, dlc_interface.get_metadata())
        return metadata

    def get_metadata_schema(self) -> DeepDict:
        metadata_schema = super().get_metadata_schema()
        for dlc_interface in self.dlc_interfaces:
            metadata_schema = dict_deep_update(metadata_schema, dlc_interface.get_metadata_schema())
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        for dlc_interface in self.dlc_interfaces:
            file_path = dlc_interface.source_data["file_path"]
            epoch_name = get_epoch_name(name=file_path.name)
            dlc_interface.add_to_nwbfile(
                nwbfile=nwbfile, metadata=metadata, container_name=f"PoseEstimation_{epoch_name}"
            )
