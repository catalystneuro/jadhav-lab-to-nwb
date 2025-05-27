"""Primary class for converting experiment-specific behavioral video."""
from ..utils.utils import olson_2024_get_epoch_name
from ..datainterfaces.base_video_interface import BaseVideoInterface


class Olson2024VideoInterface(BaseVideoInterface):
    """Video interface for olson_2024 conversion"""

    def get_video_name(self, file_name: str) -> str:
        epoch_name = olson_2024_get_epoch_name(name=file_name)
        video_name = "Video" + "_" + epoch_name
        return video_name

    def get_task_name(self, metadata: dict, video_name: str) -> str:
        if "SLP" in video_name:
            task_name = "Sleep"
        elif "HomeAltVisitAll" in video_name:
            task_name = "HomeAltVisitAll"
        return task_name
