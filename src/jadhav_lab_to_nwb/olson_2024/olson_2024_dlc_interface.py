"""Primary class for converting experiment-specific behavioral video."""
from ..common.utils.utils import olson_2024_get_epoch_name
from ..datainterfaces.base_dlc_interface import BaseDeepLabCutInterface


class Olson2024DeepLabCutInterface(BaseDeepLabCutInterface):
    """DeepLabCut interface for olson_2024 conversion"""

    def get_subject_name(self, file_name: str, subject_id: str | None = None) -> str:
        return "ind1"

    def get_pose_estimation_metadata_key(self, file_name: str, subject_id: str | None = None) -> str:
        epoch_name = olson_2024_get_epoch_name(name=file_name)
        pose_estimation_metadata_key = f"PoseEstimation_{epoch_name}"
        return pose_estimation_metadata_key

    def get_task_name(self, dlc_interface) -> str:
        file_path = dlc_interface.source_data["file_path"]
        if "SLP" in file_path.name:
            task_name = "Sleep"
        elif "HomeAltVisitAll" in file_path.name:
            task_name = "HomeAltVisitAll"
        return task_name
