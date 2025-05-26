"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile

from ..common.utils.utils import rivera_and_shukla_2025_get_epoch_name
from ..datainterfaces.base_epoch_interface import BaseEpochInterface


class RiveraAndShukla2025EpochInterface(BaseEpochInterface):
    """Epoch interface for rivera_and_shukla_2025 conversion"""

    def add_epochs_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        timestamps = self.get_timestamps()
        video_timestamps_file_paths = self.source_data["video_timestamps_file_paths"]
        subject_id = metadata["Subject"]["subject_id"]

        for epoch_timestamps, video_timestamps_file_path in zip(timestamps, video_timestamps_file_paths):
            epoch_name = rivera_and_shukla_2025_get_epoch_name(video_timestamps_file_path.name)
            epoch_number, subject_id1, subject_id2 = epoch_name.split("-")
            start_time = epoch_timestamps[0]
            stop_time = epoch_timestamps[-1]
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
