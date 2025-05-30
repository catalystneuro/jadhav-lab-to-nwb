"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from pathlib import Path
import pandas as pd
import numpy as np
import warnings
from natsort import natsorted

from jadhav_lab_to_nwb.rivera_and_shukla_2025 import (
    RiveraAndShukla2025BehaviorInterface,
    RiveraAndShukla2025VideoInterface,
    RiveraAndShukla2025DeepLabCutInterface,
    RiveraAndShukla2025EpochInterface,
)

from ..tools.spikegadgets import readCameraModuleTimeStamps
from ..utils.utils import rivera_and_shukla_2025_get_epoch_name


class RiveraAndShukla2025NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Video=RiveraAndShukla2025VideoInterface,
        Behavior=RiveraAndShukla2025BehaviorInterface,
        DeepLabCut1=RiveraAndShukla2025DeepLabCutInterface,
        DeepLabCut2=RiveraAndShukla2025DeepLabCutInterface,
        Epoch=RiveraAndShukla2025EpochInterface,
    )

    def temporally_align_data_interfaces(self, metadata: dict | None = None, conversion_options: dict | None = None):
        if "DeepLabCut1" in self.data_interface_objects:
            epoch_name_to_dlc1_interfaces = {}
            for dlc_interface in self.data_interface_objects["DeepLabCut1"].dlc_interfaces:
                file_path = Path(dlc_interface.source_data["file_path"])
                epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_path.name)
                if epoch_name not in epoch_name_to_dlc1_interfaces:
                    epoch_name_to_dlc1_interfaces[epoch_name] = [dlc_interface]
                else:
                    epoch_name_to_dlc1_interfaces[epoch_name].append(dlc_interface)
        if "DeepLabCut2" in self.data_interface_objects:
            epoch_name_to_dlc2_interfaces = {}
            for dlc_interface in self.data_interface_objects["DeepLabCut2"].dlc_interfaces:
                file_path = Path(dlc_interface.source_data["file_path"])
                epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_path.name)
                if epoch_name not in epoch_name_to_dlc2_interfaces:
                    epoch_name_to_dlc2_interfaces[epoch_name] = [dlc_interface]
                else:
                    epoch_name_to_dlc2_interfaces[epoch_name].append(dlc_interface)

        video_timestamps_file_paths = self.data_interface_objects["Video"].video_timestamps_file_paths

        # Check for clock resets
        INTER_EPOCH_INTERVAL = 1800  # Typical interval between epochs in seconds
        start_times, stop_times, clock_resets = [], [], []
        i = 0
        for epoch_video_timestamps_file_paths in video_timestamps_file_paths:
            if not isinstance(epoch_video_timestamps_file_paths, list):
                epoch_video_timestamps_file_paths = [epoch_video_timestamps_file_paths]

            for timestamp_file_path in epoch_video_timestamps_file_paths:
                timestamps, _ = readCameraModuleTimeStamps(timestamp_file_path)

                start_time = timestamps[0]
                stop_time = timestamps[-1]
                start_times.append(start_time)
                stop_times.append(stop_time)
                if i == 0:
                    i += 1
                    continue
                if start_time < stop_times[i - 1]:
                    clock_resets.append(i)
                i += 1

        # Align interface timestamps
        epoch_name_to_video_interface = {}
        video_interfaces = self.data_interface_objects["Video"].video_interfaces
        aligned_timestamps, starting_time_shifts, clock_rates, starting_frames = [], [], [], []
        i = 0
        for epoch_video_timestamps_file_paths, video_interface in zip(
            video_timestamps_file_paths, video_interfaces, strict=True
        ):
            if not isinstance(epoch_video_timestamps_file_paths, list):
                epoch_video_timestamps_file_paths = [epoch_video_timestamps_file_paths]
            epoch_name = rivera_and_shukla_2025_get_epoch_name(name=Path(epoch_video_timestamps_file_paths[0]).name)
            epoch_name_to_video_interface[epoch_name] = video_interface

            epoch_timestamps, epoch_clock_rates, epoch_starting_time_shifts, epoch_starting_frames = [], [], [], []
            for segment_index, timestamp_file_path in enumerate(epoch_video_timestamps_file_paths):
                timestamps, clock_rate = readCameraModuleTimeStamps(timestamp_file_path)

                # Calculate starting time shift for this segment
                starting_time_shift = 0.0
                for reset_index in clock_resets:
                    if i >= reset_index:
                        starting_time_shift += stop_times[reset_index - 1] + INTER_EPOCH_INTERVAL
                timestamps += starting_time_shift

                # Calculate starting frame for this segment
                starting_frame = 0
                if segment_index > 0:
                    starting_frame = epoch_starting_frames[segment_index - 1] + len(epoch_timestamps[segment_index - 1])

                epoch_timestamps.append(timestamps)
                epoch_clock_rates.append(clock_rate)
                epoch_starting_time_shifts.append(starting_time_shift)
                epoch_starting_frames.append(starting_frame)
                i += 1
            aligned_timestamps.append(epoch_timestamps)
            starting_time_shifts.append(epoch_starting_time_shifts[0])
            clock_rates.append(epoch_clock_rates[0])
            starting_frames.append(epoch_starting_frames)

            video_interface.set_aligned_timestamps(aligned_timestamps=epoch_timestamps)

        self.data_interface_objects["Video"].set_starting_frames(starting_frames=starting_frames)
        self.data_interface_objects["Epoch"].set_aligned_timestamps(aligned_timestamps=aligned_timestamps)
        self.data_interface_objects["Behavior"].set_epoch_starting_time_shifts(
            starting_time_shifts=starting_time_shifts
        )
        self.data_interface_objects["Behavior"].set_clock_rates(clock_rates=clock_rates)

        if "DeepLabCut1" in self.data_interface_objects:
            for epoch_name, dlc1_interfaces in epoch_name_to_dlc1_interfaces.items():
                video_interface = epoch_name_to_video_interface[epoch_name]
                aligned_timestamps = video_interface.get_timestamps()
                for dlc_interface, timestamps in zip(dlc1_interfaces, aligned_timestamps, strict=True):
                    self.align_dlc_interface(timestamps, dlc_interface)
        if "DeepLabCut2" in self.data_interface_objects:
            for epoch_name, dlc2_interfaces in epoch_name_to_dlc2_interfaces.items():
                video_interface = epoch_name_to_video_interface[epoch_name]
                aligned_timestamps = video_interface.get_timestamps()
                for dlc_interface, timestamps in zip(dlc2_interfaces, aligned_timestamps, strict=True):
                    self.align_dlc_interface(timestamps, dlc_interface)

    def align_dlc_interface(self, aligned_timestamps: np.ndarray, dlc_interface):
        file_path = Path(dlc_interface.source_data["file_path"])
        if ".h5" in file_path.suffixes:
            df = pd.read_hdf(file_path)
        elif ".csv" in file_path.suffixes:
            df = pd.read_csv(file_path, header=[0, 1, 2], index_col=0)
        if df.shape[0] != len(aligned_timestamps):
            msg = (
                f"Number of rows in the DLC file ({df.shape[0]}) does not match the number of aligned timestamps "
                f"({len(aligned_timestamps)}). Setting aligned timestamps to NaN."
            )
            warnings.warn(msg)
            aligned_timestamps = np.ones((df.shape[0],)) * np.nan
        dlc_interface.set_aligned_timestamps(aligned_timestamps=aligned_timestamps)
