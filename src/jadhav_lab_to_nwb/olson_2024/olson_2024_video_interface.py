"""Video interface for Olson 2024 dataset conversion.

This module provides the video data interface for converting behavioral video data
from the Olson 2024 electrophysiology dataset. It handles video file processing
and integration with NWB format for behavioral analysis.
"""
from ..utils.utils import olson_2024_get_epoch_name
from ..datainterfaces.base_video_interface import BaseVideoInterface


class Olson2024VideoInterface(BaseVideoInterface):
    """Data interface for converting Olson 2024 behavioral video data to NWB format.

    This interface extends the base video interface to handle dataset-specific
    naming conventions and task identification for the Olson 2024
    electrophysiology experiments with behavioral video recording.
    """

    def get_video_name(self, file_name: str) -> str:
        """Generate video name from file name.

        Parameters
        ----------
        file_name : str
            Name of the video file.

        Returns
        -------
        str
            Video name in format "Video_{epoch_name}".
        """
        epoch_name = olson_2024_get_epoch_name(name=file_name)
        video_name = "Video" + "_" + epoch_name
        return video_name

    def get_task_name(self, metadata: dict, video_name: str) -> str:
        """Determine task name from video name.

        Parameters
        ----------
        metadata : dict
            Metadata dictionary (not used in this implementation).
        video_name : str
            Name of the video.

        Returns
        -------
        str
            Task name based on video name content ("Sleep" or "HomeAltVisitAll").
        """
        if "SLP" in video_name:
            task_name = "Sleep"
        elif "HomeAltVisitAll" in video_name:
            task_name = "HomeAltVisitAll"
        return task_name
