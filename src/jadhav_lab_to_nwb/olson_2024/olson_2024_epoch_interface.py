"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile

from ..utils.utils import olson_2024_get_epoch_name
from ..datainterfaces.base_epoch_interface import BaseEpochInterface


class Olson2024EpochInterface(BaseEpochInterface):
    """Epoch interface for olson_2024 conversion"""

    def add_epochs_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        timestamps = self.get_timestamps()
        video_timestamps_file_paths = self.source_data["video_timestamps_file_paths"]
        for epoch_timestamps, video_timestamps_file_path in zip(timestamps, video_timestamps_file_paths):
            epoch_name = olson_2024_get_epoch_name(video_timestamps_file_path.name)
            epoch_id, _, _, _ = epoch_name.split("_")
            start_time = epoch_timestamps[0][0]
            stop_time = epoch_timestamps[-1][-1]
            tag = epoch_id[1:]  # from S01 to 01
            epoch_number = int(tag)
            if "SLP" in epoch_name:
                task_name = "Sleep"
                task_metadata = next(meta for meta in metadata["Tasks"] if meta["name"] == task_name)
                task_epochs = task_metadata.get("task_epochs", [])
                task_epochs.append(epoch_number)
                task_metadata["task_epochs"] = task_epochs
            elif "HomeAltVisitAll" in epoch_name:
                task_name = "HomeAltVisitAll"
                task_metadata = next(meta for meta in metadata["Tasks"] if meta["name"] == task_name)
                task_epochs = task_metadata.get("task_epochs", [])
                task_epochs.append(epoch_number)
                task_metadata["task_epochs"] = task_epochs
            else:
                raise ValueError(f"Unknown task for epoch {epoch_name}")

            nwbfile.add_epoch(
                start_time=start_time,
                stop_time=stop_time,
                tags=[tag],
            )
