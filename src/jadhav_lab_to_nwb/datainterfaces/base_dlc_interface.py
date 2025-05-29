"""Primary class for converting experiment-specific behavioral video."""
from abc import abstractmethod
from pynwb.file import NWBFile
from pydantic import FilePath

from neuroconv.utils import DeepDict, dict_deep_update
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import DeepLabCutInterface

from ..utils.utils import rivera_and_shukla_2025_get_epoch_name


class BaseDeepLabCutInterface(BaseDataInterface):
    """DeepLabCut interface for rivera_and_shukla_2025 conversion"""

    keywords = ("DLC",)

    def __init__(
        self,
        file_paths: list[list[FilePath] | FilePath],
        config_file_paths: list[list[FilePath] | FilePath] | None = None,
        subject_id: str | None = None,
        verbose: bool = True,
    ):
        # file_paths must be sorted in the order that the videos were recorded
        assert len(file_paths) > 0, "At least one file path must be provided."
        if config_file_paths is None:
            config_file_paths = [[None] * len(fp) if isinstance(fp, list) else None for fp in file_paths]
        msg = "The number of file paths must match the number of config file paths."
        assert len(file_paths) == len(config_file_paths), msg
        dlc_interfaces = []
        for epoch_file_paths, epoch_config_file_paths in zip(file_paths, config_file_paths):
            if not isinstance(epoch_file_paths, list):
                epoch_file_paths = [epoch_file_paths]
            if not isinstance(epoch_config_file_paths, list):
                epoch_config_file_paths = [epoch_config_file_paths]
            assert len(epoch_file_paths) == len(epoch_config_file_paths), msg
            for file_path, config_file_path in zip(epoch_file_paths, epoch_config_file_paths):
                subject_name = self.get_subject_name(file_name=file_path.name, subject_id=subject_id)
                pose_estimation_metadata_key = self.get_pose_estimation_metadata_key(
                    file_name=file_path.name, subject_id=subject_id
                )
                dlc_interface = DeepLabCutInterface(
                    file_path=file_path,
                    config_file_path=config_file_path,
                    subject_name=subject_name,
                    pose_estimation_metadata_key=pose_estimation_metadata_key,
                    verbose=verbose,
                )
                dlc_interfaces.append(dlc_interface)
        self.dlc_interfaces = dlc_interfaces

    @abstractmethod
    def get_subject_name(self, file_name: str, subject_id: str | None = None) -> str:
        pass

    @abstractmethod
    def get_pose_estimation_metadata_key(self, file_name: str, subject_id: str | None = None) -> str:
        pass

    @abstractmethod
    def get_task_name(self, dlc_interface: DeepLabCutInterface) -> str:
        pass

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        for dlc_interface in self.dlc_interfaces:
            interface_metadata = dlc_interface.get_metadata()
            dict_deep_update(metadata, interface_metadata)
        return metadata

    def get_metadata_schema(self) -> DeepDict:
        metadata_schema = super().get_metadata_schema()
        for dlc_interface in self.dlc_interfaces:
            metadata_schema = dict_deep_update(metadata_schema, dlc_interface.get_metadata_schema())
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        for dlc_interface in self.dlc_interfaces:
            # Update the metadata to connect camera_device from Video to PoseEstimation
            pem_key = dlc_interface.pose_estimation_metadata_key
            task_name = self.get_task_name(dlc_interface=dlc_interface)
            task_metadata = next(meta for meta in metadata["Tasks"] if meta["name"] == task_name)
            camera_id = task_metadata["camera_id"][0]
            device_name = f"camera_device {camera_id}"
            metadata["PoseEstimation"]["PoseEstimationContainers"][pem_key]["devices"] = [device_name]
            metadata["PoseEstimation"]["Devices"][device_name] = dict(name=device_name)

            dlc_interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)
