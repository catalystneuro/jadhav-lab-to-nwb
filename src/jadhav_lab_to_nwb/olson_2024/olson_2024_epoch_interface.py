"""Epoch interface for Olson 2024 dataset conversion.

This module provides the epoch data interface for converting experimental epoch
information from the Olson 2024 electrophysiology dataset. It handles epoch
boundaries and task assignments for different experimental conditions.
"""
from pynwb.file import NWBFile

from ..utils.utils import olson_2024_get_epoch_name
from ..datainterfaces.base_epoch_interface import BaseEpochInterface


class Olson2024EpochInterface(BaseEpochInterface):
    """Data interface for converting Olson 2024 experimental epoch data to NWB format.

    This interface extends the base epoch interface to handle dataset-specific
    epoch naming conventions and task assignments for the Olson 2024
    electrophysiology experiments.
    """

    def add_epochs_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        """Add experimental epochs to the NWB file with task assignments.

        Processes video timestamp files to extract epoch boundaries and assigns
        epochs to appropriate tasks based on naming conventions. Updates task
        metadata with epoch assignments for Sleep and HomeAltVisitAll tasks.

        Parameters
        ----------
        nwbfile : NWBFile
            The NWB file object to add epochs to.
        metadata : dict
            Metadata dictionary containing task definitions that will be updated
            with epoch assignments.

        Raises
        ------
        ValueError
            If epoch name doesn't match expected task patterns (SLP or HomeAltVisitAll).
        """
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
