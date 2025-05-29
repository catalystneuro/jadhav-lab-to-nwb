"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter

from jadhav_lab_to_nwb.rivera_and_shukla_2025 import (
    RiveraAndShukla2025BehaviorInterface,
    RiveraAndShukla2025VideoInterface,
    RiveraAndShukla2025DeepLabCutInterface,
    RiveraAndShukla2025EpochInterface,
)

from ..tools.spikegadgets import readCameraModuleTimeStamps


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
        video_interfaces = self.data_interface_objects["Video"].video_interfaces
        aligned_timestamps, starting_time_shifts, clock_rates, starting_frames = [], [], [], []
        i = 0
        for epoch_video_timestamps_file_paths, video_interface in zip(video_timestamps_file_paths, video_interfaces):
            if not isinstance(epoch_video_timestamps_file_paths, list):
                epoch_video_timestamps_file_paths = [epoch_video_timestamps_file_paths]

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

            # # For DLC interfaces, use the first timestamp array (assuming one DLC per epoch)
            # if "DeepLabCut1" in self.data_interface_objects:
            #     dlc1_interface = self.data_interface_objects["DeepLabCut1"].dlc_interfaces[i]
            #     dlc1_interface.set_aligned_timestamps(aligned_timestamps=aligned_epoch_timestamps[0])
            # if "DeepLabCut2" in self.data_interface_objects:
            #     dlc2_interface = self.data_interface_objects["DeepLabCut2"].dlc_interfaces[i]
            #     dlc2_interface.set_aligned_timestamps(aligned_timestamps=aligned_epoch_timestamps[0])

        self.data_interface_objects["Video"].set_starting_frames(starting_frames=starting_frames)
        self.data_interface_objects["Epoch"].set_aligned_timestamps(aligned_timestamps=aligned_timestamps)
        self.data_interface_objects["Behavior"].set_epoch_starting_time_shifts(
            starting_time_shifts=starting_time_shifts
        )
        self.data_interface_objects["Behavior"].set_clock_rates(clock_rates=clock_rates)
