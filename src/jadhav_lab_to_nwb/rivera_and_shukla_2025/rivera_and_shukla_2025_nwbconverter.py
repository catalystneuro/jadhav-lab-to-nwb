"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter

from jadhav_lab_to_nwb.rivera_and_shukla_2025 import (
    RiveraAndShukla2025BehaviorInterface,
    RiveraAndShukla2025VideoInterface,
    RiveraAndShukla2025DeepLabCutInterface,
    RiveraAndShukla2025EpochInterface,
)

from ..common.tools.spikegadgets import readCameraModuleTimeStamps


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
        for i, video_timestamps_file_path in enumerate(video_timestamps_file_paths):
            timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
            start_time = timestamps[0]
            stop_time = timestamps[-1]
            start_times.append(start_time)
            stop_times.append(stop_time)
            if i == 0:
                continue
            if start_time < stop_times[i - 1]:
                clock_resets.append(i)

        # Align interface timestamps
        video_interfaces = self.data_interface_objects["Video"].video_interfaces
        dlc1_interfaces = self.data_interface_objects["DeepLabCut1"].dlc_interfaces
        dlc2_interfaces = self.data_interface_objects["DeepLabCut2"].dlc_interfaces
        aligned_timestamps, starting_time_shifts, clock_rates = [], [], []
        for i, (video_timestamps_file_path, video_interface, dlc1_interface, dlc2_interface) in enumerate(
            zip(video_timestamps_file_paths, video_interfaces, dlc1_interfaces, dlc2_interfaces)
        ):
            timestamps, clock_rate = readCameraModuleTimeStamps(video_timestamps_file_path)
            starting_time_shift = 0.0
            for reset_index in clock_resets:
                if i >= reset_index:
                    starting_time_shift += stop_times[reset_index - 1] + INTER_EPOCH_INTERVAL
            timestamps += starting_time_shift
            starting_time_shifts.append(starting_time_shift)
            clock_rates.append(clock_rate)

            video_interface.set_aligned_timestamps(aligned_timestamps=[timestamps])
            dlc1_interface.set_aligned_timestamps(aligned_timestamps=timestamps)
            dlc2_interface.set_aligned_timestamps(aligned_timestamps=timestamps)
            aligned_timestamps.append(timestamps)
        self.data_interface_objects["Epoch"].set_aligned_timestamps(aligned_timestamps=aligned_timestamps)
        self.data_interface_objects["Behavior"].set_epoch_starting_time_shifts(
            starting_time_shifts=starting_time_shifts
        )
        self.data_interface_objects["Behavior"].set_clock_rates(clock_rates=clock_rates)
