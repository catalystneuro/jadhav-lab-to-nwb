"""Primary class for converting experiment-specific behavioral video."""
from neuroconv.utils import DeepDict, dict_deep_update

from ..utils.utils import rivera_and_shukla_2025_get_epoch_name
from ..datainterfaces.base_dlc_interface import BaseDeepLabCutInterface


class RiveraAndShukla2025DeepLabCutInterface(BaseDeepLabCutInterface):
    """DeepLabCut interface for rivera_and_shukla_2025 conversion"""

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        for dlc_interface in self.dlc_interfaces:
            interface_metadata = dlc_interface.get_metadata()
            pem_key = dlc_interface.pose_estimation_metadata_key
            skeleton_key = f"Skeleton{pem_key}_{dlc_interface.subject_name.capitalize()}"
            subject_id = pem_key.split("-")[-1]
            interface_metadata["PoseEstimation"]["Skeletons"][skeleton_key]["subject"] = subject_id
            skeleton_name = f"Skeleton{pem_key}"
            interface_metadata["PoseEstimation"]["Skeletons"][skeleton_key]["name"] = skeleton_name
            dict_deep_update(metadata, interface_metadata)
        return metadata

    def get_subject_name(self, file_name: str, subject_id: str | None = None) -> str:
        epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_name)
        epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
        subject_name = "rat 1" if subject_id1 == subject_id else "rat 2"
        return subject_name

    def get_pose_estimation_metadata_key(self, file_name: str, subject_id: str | None = None) -> str:
        epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_name)
        segment_number = file_name.split(").")[1].split("DLC")[0]
        epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
        subject_id = subject_id1 if subject_id1 == subject_id else subject_id2
        pose_estimation_metadata_key = f"PoseEstimation_{epoch_number}-{subject_id}-{segment_number}"
        return pose_estimation_metadata_key

    def get_task_name(self, dlc_interface) -> str:
        subject_name = dlc_interface.subject_name
        if subject_name == "rat 1":
            task_name = "SocialW_Left"
        elif subject_name == "rat 2":
            task_name = "SocialW_Right"
        return task_name
