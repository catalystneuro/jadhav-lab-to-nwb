"""DeepLabCut interface for Rivera and Shukla 2025 dataset conversion.

This module provides the interface for converting DeepLabCut pose estimation data
from the Rivera and Shukla 2025 social behavior experiment to NWB format. It handles
the parsing of pose estimation files and implements experiment-specific logic for
subject identification and task association.
"""
from neuroconv.utils import DeepDict, dict_deep_update

from ..utils.utils import rivera_and_shukla_2025_get_epoch_name
from ..datainterfaces.base_dlc_interface import BaseDeepLabCutInterface


class RiveraAndShukla2025DeepLabCutInterface(BaseDeepLabCutInterface):
    """DeepLabCut interface for Rivera and Shukla 2025 social behavior dataset.

    This interface handles the conversion of DeepLabCut pose estimation data from
    social behavior experiments involving two rats. It implements experiment-specific
    logic for subject identification, task assignment, and metadata organization
    based on file naming conventions and experimental design.

    The interface processes pose estimation files for multi-subject experiments
    and creates appropriate skeleton metadata with subject associations and task
    assignments for social behavior analysis.

    Notes
    -----
    This interface is specifically designed for the Rivera and Shukla 2025 dataset
    which involves social behavior experiments with two subjects (rats) and requires
    custom logic for subject identification and task assignment based on spatial
    positioning (left/right).
    """

    def get_metadata(self) -> DeepDict:
        """Get metadata for pose estimation with subject-specific skeleton information.

        Extends the base metadata to include subject associations and skeleton
        naming conventions specific to the Rivera and Shukla 2025 social behavior
        experiment. Creates skeleton metadata with proper subject identification
        and naming for multi-subject pose estimation data.

        Returns
        -------
        DeepDict
            Metadata dictionary containing pose estimation configuration with
            subject-specific skeleton information, including subject IDs and
            skeleton names for each DLC interface.
        """
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
        """Determine subject name from file name and subject ID.

        Parses the file name to extract epoch information and determines
        which subject (rat 1 or rat 2) the pose estimation data corresponds
        to based on the provided subject ID.

        Parameters
        ----------
        file_name : str
            Name of the DeepLabCut pose estimation file.
        subject_id : str | None, optional
            Subject identifier to match against epoch naming convention.

        Returns
        -------
        str
            Subject name ("rat 1" or "rat 2") based on subject ID matching.
        """
        epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_name)
        epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
        subject_name = "rat 1" if subject_id1 == subject_id else "rat 2"
        return subject_name

    def get_pose_estimation_metadata_key(self, file_name: str, subject_id: str | None = None) -> str:
        """Generate pose estimation metadata key from file name and subject ID.

        Creates a unique metadata key for pose estimation data based on the
        file naming convention. The key includes epoch number, subject ID,
        and segment number for proper organization of multi-subject,
        multi-segment pose estimation data.

        Parameters
        ----------
        file_name : str
            Name of the DeepLabCut pose estimation file.
        subject_id : str | None, optional
            Subject identifier to include in the metadata key.

        Returns
        -------
        str
            Formatted metadata key in the format "PoseEstimation_{epoch}-{subject}-{segment}".
        """
        epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_name)
        segment_number = file_name.split(").")[1].split("DLC")[0]
        epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
        subject_id = subject_id1 if subject_id1 == subject_id else subject_id2
        pose_estimation_metadata_key = f"PoseEstimation_{epoch_number}-{subject_id}-{segment_number}"
        return pose_estimation_metadata_key

    def get_task_name(self, dlc_interface) -> str:
        """Determine task name based on subject spatial positioning.

        Assigns task names based on the subject's spatial position in the
        social behavior experiment. Rat 1 is assigned to the left position
        and rat 2 to the right position in the social interaction setup.

        Parameters
        ----------
        dlc_interface : object
            DeepLabCut interface object containing subject information.
            Must have a subject_name attribute.

        Returns
        -------
        str
            Task name ("SocialW_Left" or "SocialW_Right") based on subject positioning.
        """
        subject_name = dlc_interface.subject_name
        if subject_name == "rat 1":
            task_name = "SocialW_Left"
        elif subject_name == "rat 2":
            task_name = "SocialW_Right"
        return task_name
