"""Epoch interface for Rivera and Shukla 2025 dataset conversion.

This module provides the interface for converting epoch data from the Rivera and
Shukla 2025 social behavior experiment to NWB format. It handles the creation of
epoch tables with proper temporal boundaries and task associations for multi-subject
social behavior experiments.
"""
from pynwb.file import NWBFile

from ..utils.utils import rivera_and_shukla_2025_get_epoch_name
from ..datainterfaces.base_epoch_interface import BaseEpochInterface


class RiveraAndShukla2025EpochInterface(BaseEpochInterface):
    """Epoch interface for Rivera and Shukla 2025 social behavior dataset.

    This interface handles the conversion of epoch data from social behavior
    experiments involving two subjects. It creates epoch tables with proper
    temporal boundaries derived from video timestamps and associates epochs
    with appropriate tasks based on subject positioning and experimental design.
    """

    def add_epochs_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        """Add epoch data to NWB file with subject-specific task associations.

        Creates epoch entries in the NWB file based on video timestamp boundaries
        and associates each epoch with the appropriate task based on the subject's
        spatial positioning in the social behavior experiment.

        Parameters
        ----------
        nwbfile : NWBFile
            The NWB file object to add epoch data to.
        metadata : dict
            Metadata dictionary containing subject information and task definitions.
        """
        timestamps = self.get_timestamps()
        video_timestamps_file_paths = self.source_data["video_timestamps_file_paths"]
        subject_id = metadata["Subject"]["subject_id"]

        for epoch_timestamps, epoch_video_timestamps_file_paths in zip(timestamps, video_timestamps_file_paths):
            epoch_name = rivera_and_shukla_2025_get_epoch_name(epoch_video_timestamps_file_paths[0].name)
            epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
            start_time = epoch_timestamps[0][0]
            stop_time = epoch_timestamps[-1][-1]
            tag = f"{int(epoch_number):02d}"  # Spyglass requires 2-digit string epoch numbers
            nwbfile.add_epoch(
                start_time=start_time,
                stop_time=stop_time,
                tags=[tag],
            )
            if subject_id == subject_id1:
                task_name = "SocialW_Left"
                task_metadata = next(meta for meta in metadata["Tasks"] if meta["name"] == task_name)
                task_epochs = task_metadata.get("task_epochs", [])
                task_epochs.append(epoch_number)
                task_metadata["task_epochs"] = task_epochs
            elif subject_id == subject_id2:
                task_name = "SocialW_Right"
                task_metadata = next(meta for meta in metadata["Tasks"] if meta["name"] == task_name)
                task_epochs = task_metadata.get("task_epochs", [])
                task_epochs.append(epoch_number)
                task_metadata["task_epochs"] = task_epochs
