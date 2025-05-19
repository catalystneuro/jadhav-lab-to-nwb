"""Primary class for converting experiment-specific behavioral video."""
from pynwb.file import NWBFile
from pydantic import FilePath
from typing import Optional

from neuroconv.utils import DeepDict, dict_deep_update
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import DeepLabCutInterface

from .utils.utils import get_epoch_name
from ..olson_2024.tools.spikegadgets import readCameraModuleTimeStamps


class RiveraAndShukla2025DeepLabCutInterface(BaseDataInterface):
    """DeepLabCut interface for rivera_and_shukla_2025 conversion"""

    keywords = ("DLC",)

    def __init__(
        self,
        file_paths: list[FilePath],
        config_file_paths: Optional[list[FilePath]] = None,
        video_timestamps_file_paths: Optional[list[FilePath]] = None,
        subject_id: str | None = None,
        verbose: bool = True,
    ):
        # file_paths must be sorted in the order that the videos were recorded
        assert len(file_paths) > 0, "At least one file path must be provided."
        if config_file_paths is None:
            config_file_paths = [None] * len(file_paths)
        if video_timestamps_file_paths is None:
            video_timestamps_file_paths = [None] * len(file_paths)
        msg = "The number of file paths must match the number of config file paths and the number of video_timestamps file paths."
        assert len(file_paths) == len(config_file_paths) == len(video_timestamps_file_paths), msg
        dlc_interfaces = []
        for file_path, config_file_path in zip(file_paths, config_file_paths):
            epoch_name = get_epoch_name(name=file_path.name)
            epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
            subject_name = "rat 1" if subject_id1 == subject_id else "rat 2"
            subject_id = subject_id1 if subject_id1 == subject_id else subject_id2
            pose_estimation_metadata_key = f"PoseEstimation_{epoch_number}-{subject_id}"
            dlc_interface = DeepLabCutInterface(
                file_path=file_path,
                config_file_path=config_file_path,
                subject_name=subject_name,
                pose_estimation_metadata_key=pose_estimation_metadata_key,
                verbose=verbose,
            )
            dlc_interfaces.append(dlc_interface)
        self.dlc_interfaces = dlc_interfaces
        self.video_timestamps_file_paths = video_timestamps_file_paths

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        for dlc_interface in self.dlc_interfaces:
            interface_metadata = dlc_interface.get_metadata()
            skeleton_name = (
                f"Skeleton{dlc_interface.pose_estimation_metadata_key}_{dlc_interface.subject_name.capitalize()}"
            )
            subject_id = dlc_interface.pose_estimation_metadata_key.split("-")[-1]
            interface_metadata["PoseEstimation"]["Skeletons"][skeleton_name]["subject"] = subject_id
            new_skeleton_name = f"Skeleton{dlc_interface.pose_estimation_metadata_key}"
            interface_metadata["PoseEstimation"]["Skeletons"][skeleton_name]["name"] = new_skeleton_name
            metadata = dict_deep_update(metadata, interface_metadata)
        return metadata

    def get_metadata_schema(self) -> DeepDict:
        metadata_schema = super().get_metadata_schema()
        for dlc_interface in self.dlc_interfaces:
            metadata_schema = dict_deep_update(metadata_schema, dlc_interface.get_metadata_schema())
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        for dlc_interface, video_timestamps_file_path in zip(self.dlc_interfaces, self.video_timestamps_file_paths):
            if video_timestamps_file_path is not None:
                timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
                dlc_interface.set_aligned_timestamps(aligned_timestamps=timestamps)
            dlc_interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)
