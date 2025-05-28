"""Primary class for converting experiment-specific behavioral video."""
from ..utils.utils import rivera_and_shukla_2025_get_epoch_name
from ..datainterfaces.base_video_interface import BaseVideoInterface


class RiveraAndShukla2025VideoInterface(BaseVideoInterface):
    """Video interface for rivera_and_shukla_2025 conversion"""

    def get_video_name(self, file_name: str) -> str:
        """Extracts the video name from the file name."""
        epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_name)
        return "Video_" + epoch_name

    def get_task_name(self, metadata: dict, video_name: str) -> str:
        epoch_name = video_name.split("_")[-1]  # ex. Video_1-XFN1-XFN3 --> 1-XFN1-XFN3
        epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
        if metadata["Subject"]["subject_id"] == subject_id1:
            task_name = "SocialW_Left"
        elif metadata["Subject"]["subject_id"] == subject_id2:
            task_name = "SocialW_Right"
        return task_name
