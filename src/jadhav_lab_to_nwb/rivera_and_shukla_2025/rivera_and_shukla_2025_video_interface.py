"""Video interface for Rivera and Shukla 2025 dataset conversion.

This module provides the interface for converting video data from the Rivera and
Shukla 2025 social behavior experiment to NWB format. It handles video file
processing with experiment-specific naming conventions and task associations
for multi-subject social behavior experiments.
"""
from ..utils.utils import rivera_and_shukla_2025_get_epoch_name
from ..datainterfaces.base_video_interface import BaseVideoInterface


class RiveraAndShukla2025VideoInterface(BaseVideoInterface):
    """Video interface for Rivera and Shukla 2025 social behavior dataset.

    This interface handles the conversion of video data from social behavior
    experiments involving two subjects. It implements experiment-specific logic
    for video naming conventions and task associations based on subject
    positioning and experimental design.

    The interface processes video files with proper naming and task assignment
    for multi-subject behavioral experiments, ensuring correct organization
    within the NWB file structure.

    Notes
    -----
    This interface is specifically designed for the Rivera and Shukla 2025 dataset
    which involves social behavior experiments with two subjects and requires
    task assignment based on spatial positioning (left/right).
    """

    def get_video_name(self, file_name: str) -> str:
        """Generate video name from file name using epoch naming convention.

        Extracts the epoch name from the video file name and formats it
        according to the Rivera and Shukla 2025 naming convention.

        Parameters
        ----------
        file_name : str
            Name of the video file to extract epoch information from.

        Returns
        -------
        str
            Formatted video name in the format "Video_{epoch_name}".
        """
        epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_name)
        return "Video_" + epoch_name

    def get_task_name(self, metadata: dict, video_name: str) -> str:
        """Determine task name based on subject positioning in social behavior experiment.

        Analyzes the video name and subject metadata to assign the appropriate
        task name based on spatial positioning. Subject 1 is assigned to the
        left position (SocialW_Left) and subject 2 to the right position
        (SocialW_Right) in the social interaction setup.

        Parameters
        ----------
        metadata : dict
            Metadata dictionary containing subject information. Must include
            'Subject' with 'subject_id' field.
        video_name : str
            Name of the video in the format "Video_{epoch_name}" where
            epoch_name contains subject identifiers.

        Returns
        -------
        str
            Task name ("SocialW_Left" or "SocialW_Right") based on subject positioning.

        Raises
        ------
        ValueError
            If the metadata subject ID does not match either expected subject ID
            from the epoch naming convention.
        """
        epoch_name = video_name.split("_")[-1]  # ex. Video_1-XFN1-XFN3 --> 1-XFN1-XFN3
        epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
        if metadata["Subject"]["subject_id"] == subject_id1:
            task_name = "SocialW_Left"
        elif metadata["Subject"]["subject_id"] == subject_id2:
            task_name = "SocialW_Right"
        else:
            message = (
                f"Metadata subject ID {metadata['Subject']['subject_id']} does not match the expected subject IDs "
                f"{subject_id1} or {subject_id2}."
            )
            raise ValueError(message)
        return task_name
