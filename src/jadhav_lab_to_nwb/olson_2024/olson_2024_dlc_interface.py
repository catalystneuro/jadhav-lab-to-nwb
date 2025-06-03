"""DeepLabCut interface for Olson 2024 dataset conversion.

This module provides the DeepLabCut pose estimation interface for converting
behavioral tracking data from the Olson 2024 electrophysiology dataset. It handles
pose estimation output files and integrates them with NWB format.
"""
from ..utils.utils import olson_2024_get_epoch_name
from ..datainterfaces.base_dlc_interface import BaseDeepLabCutInterface


class Olson2024DeepLabCutInterface(BaseDeepLabCutInterface):
    """Data interface for converting Olson 2024 DeepLabCut pose estimation data to NWB format.

    This interface extends the base DeepLabCut interface to handle dataset-specific
    naming conventions and task identification for the Olson 2024 electrophysiology
    experiments with behavioral tracking.
    """

    def get_subject_name(self, file_name: str, subject_id: str | None = None) -> str:
        """Get subject name for pose estimation data.

        Parameters
        ----------
        file_name : str
            Name of the DLC output file.
        subject_id : str | None, optional
            Subject identifier (not used in this implementation).

        Returns
        -------
        str
            Subject name for the Olson 2024 dataset (always "ind1").
        """
        return "ind1"

    def get_pose_estimation_metadata_key(self, file_name: str, subject_id: str | None = None) -> str:
        """Generate metadata key for pose estimation data.

        Parameters
        ----------
        file_name : str
            Name of the DLC output file.
        subject_id : str | None, optional
            Subject identifier (not used in this implementation).

        Returns
        -------
        str
            Metadata key in format "PoseEstimation_{epoch_name}".
        """
        epoch_name = olson_2024_get_epoch_name(name=file_name)
        pose_estimation_metadata_key = f"PoseEstimation_{epoch_name}"
        return pose_estimation_metadata_key

    def get_task_name(self, dlc_interface) -> str:
        """Determine task name from DLC file path.

        Parameters
        ----------
        dlc_interface : BaseDeepLabCutInterface
            DLC interface containing source data information.

        Returns
        -------
        str
            Task name based on file path content.
        """
        file_path = dlc_interface.source_data["file_path"]
        if "SLP" in file_path.name:
            task_name = "Sleep"
        elif "HomeAltVisitAll" in file_path.name:
            task_name = "HomeAltVisitAll"
        return task_name
