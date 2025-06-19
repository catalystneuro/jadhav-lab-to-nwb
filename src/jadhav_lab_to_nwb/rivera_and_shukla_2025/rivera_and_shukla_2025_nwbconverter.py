"""NWB converter for Rivera and Shukla 2025 dataset conversion.

This module provides the primary NWB converter class for the Rivera and Shukla 2025
social behavior dataset. It orchestrates the conversion of multiple data streams
(video, behavior, pose estimation, epochs) and handles temporal alignment across
all data modalities with clock reset detection and correction.
"""
from neuroconv import NWBConverter
from pathlib import Path
import pandas as pd
import numpy as np
import warnings
from pynwb import NWBFile
from neuroconv.utils import DeepDict

from jadhav_lab_to_nwb.rivera_and_shukla_2025 import (
    RiveraAndShukla2025BehaviorInterface,
    RiveraAndShukla2025VideoInterface,
    RiveraAndShukla2025DeepLabCutInterface,
    RiveraAndShukla2025EpochInterface,
)

from ..tools.spikegadgets import readCameraModuleTimeStamps
from ..utils.utils import rivera_and_shukla_2025_get_epoch_name


class RiveraAndShukla2025NWBConverter(NWBConverter):
    """NWB converter for Rivera and Shukla 2025 social behavior dataset.

    This converter orchestrates the conversion of multi-modal experimental data
    from social behavior experiments to NWB format. It handles temporal alignment
    across video, behavioral events, pose estimation, and epoch data with
    clock reset detection and correction algorithms.

    The converter manages data from two subjects simultaneously and ensures
    proper synchronization across all data streams despite potential timing
    discontinuities from recording system resets.

    Notes
    -----
    This converter is specifically designed for the Rivera and Shukla 2025 dataset
    which involves multi-subject social behavior experiments with complex temporal
    alignment requirements due to potential clock resets during long recordings.

    Attributes
    ----------
    data_interface_classes : dict
        Mapping of data interface names to their corresponding classes.
    INTER_EPOCH_INTERVAL : int
        Typical interval between epochs in seconds, used for clock reset correction.
    dlc_timestamp_mismatches : list[tuple[float, float, str]]
        List of epochs with DLC data that doesn't match video timestamps, tuple of (start_time, stop_time, comment).
    """

    data_interface_classes = dict(
        Video=RiveraAndShukla2025VideoInterface,
        Behavior=RiveraAndShukla2025BehaviorInterface,
        DeepLabCut1=RiveraAndShukla2025DeepLabCutInterface,
        DeepLabCut2=RiveraAndShukla2025DeepLabCutInterface,
        Epoch=RiveraAndShukla2025EpochInterface,
    )
    INTER_EPOCH_INTERVAL = 1800
    dlc_timestamp_mismatches: list[tuple[float, float, str]] = []

    def add_to_nwbfile(
        self, nwbfile: NWBFile, metadata: DeepDict | None = None, conversion_options: dict | None = None
    ):
        super().add_to_nwbfile(nwbfile, metadata, conversion_options)
        self.add_invalid_intervals_to_nwbfile(
            clock_resets=self.clock_resets, dlc_timestamp_mismatches=self.dlc_timestamp_mismatches, nwbfile=nwbfile
        )

    def temporally_align_data_interfaces(
        self, metadata: DeepDict | None = None, conversion_options: dict | None = None
    ):
        """Perform temporal alignment across all data interfaces.

        Orchestrates the temporal alignment of all data modalities by detecting
        clock resets, calculating aligned timestamps, and applying corrections
        to each data interface. This method ensures temporal synchronization
        across video, behavioral events, pose estimation, and epoch data.

        Parameters
        ----------
        metadata : dict | None, optional
            Metadata dictionary (not used in current implementation).
        conversion_options : dict | None, optional
            Conversion options dictionary (not used in current implementation).
        """
        aligned_timestamps, starting_time_shifts, clock_rates, starting_frames = self.get_aligned_timing()
        self.align_video(aligned_timestamps=aligned_timestamps, starting_frames=starting_frames)
        self.align_epoch(aligned_timestamps=aligned_timestamps)
        self.align_behavior(starting_time_shifts=starting_time_shifts, clock_rates=clock_rates)
        self.align_dlc()

    def get_aligned_timing(self):
        """Calculate aligned timestamps with clock reset detection and correction.

        Analyzes video timestamp files to detect clock resets and calculates
        corrected timestamps, time shifts, clock rates, and frame offsets for
        all data streams. This is the core temporal alignment algorithm.

        Returns
        -------
        tuple
            A tuple containing aligned timestamps, time shifts, clock rates, and frame offsets.
        """
        video_timestamps_file_paths = self.data_interface_objects["Video"].video_timestamps_file_paths

        # Check for clock resets
        start_times, stop_times, self.clock_resets = [], [], []
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
                    self.clock_resets.append(i)
                i += 1

        # Align timestamps with clock resets
        aligned_timestamps, starting_time_shifts, clock_rates, starting_frames = [], [], [], []
        i = 0
        for epoch_video_timestamps_file_paths in video_timestamps_file_paths:
            if not isinstance(epoch_video_timestamps_file_paths, list):
                epoch_video_timestamps_file_paths = [epoch_video_timestamps_file_paths]

            epoch_timestamps, epoch_clock_rates, epoch_starting_time_shifts, epoch_starting_frames = [], [], [], []
            for segment_index, timestamp_file_path in enumerate(epoch_video_timestamps_file_paths):
                timestamps, clock_rate = readCameraModuleTimeStamps(timestamp_file_path)

                # Calculate starting time shift for this segment
                starting_time_shift = 0.0
                for reset_index in self.clock_resets:
                    if i >= reset_index:
                        starting_time_shift += stop_times[reset_index - 1] + self.INTER_EPOCH_INTERVAL
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

        return (aligned_timestamps, starting_time_shifts, clock_rates, starting_frames)

    def align_video(self, aligned_timestamps: list[list[np.ndarray]], starting_frames: list[list[int]]):
        """Apply temporal alignment to video interfaces.

        Sets aligned timestamps and starting frame offsets for all video interfaces
        to ensure temporal synchronization across video segments and epochs.

        Parameters
        ----------
        aligned_timestamps : list[list[np.ndarray]]
            Nested list of timestamp arrays. Outer list corresponds to epochs,
            inner list corresponds to segments within each epoch.
        starting_frames : list[list[int]]
            Nested list of starting frame indices for each video segment.
        """
        video_interfaces = self.data_interface_objects["Video"].video_interfaces
        for video_interface, timestamps in zip(video_interfaces, aligned_timestamps, strict=True):
            video_interface.set_aligned_timestamps(aligned_timestamps=timestamps)
        self.data_interface_objects["Video"].set_starting_frames(starting_frames=starting_frames)

    def align_epoch(self, aligned_timestamps: list[list[np.ndarray]]):
        """Apply temporal alignment to epoch interface.

        Sets aligned timestamps for the epoch interface to ensure proper
        temporal boundaries for experimental epochs.

        Parameters
        ----------
        aligned_timestamps : list[list[np.ndarray]]
            Nested list of timestamp arrays. Outer list corresponds to epochs,
            inner list corresponds to segments within each epoch.
        """
        epoch_interface = self.data_interface_objects["Epoch"]
        epoch_interface.set_aligned_timestamps(aligned_timestamps=aligned_timestamps)

    def align_behavior(self, starting_time_shifts: list[float], clock_rates: list[float]):
        """Apply temporal alignment to behavior interface.

        Sets time shifts and clock rates for the behavior interface to ensure
        proper temporal alignment of behavioral events with other data streams.

        Parameters
        ----------
        starting_time_shifts : list[float]
            Time shift values for each epoch to account for clock resets.
        clock_rates : list[float]
            Clock rates (fps) for each epoch for timestamp conversion.
        """
        behavior_interface = self.data_interface_objects["Behavior"]
        behavior_interface.set_epoch_starting_time_shifts(starting_time_shifts=starting_time_shifts)
        behavior_interface.set_clock_rates(clock_rates=clock_rates)

    def align_dlc(self):
        """Apply temporal alignment to DeepLabCut interfaces.

        Aligns DeepLabCut pose estimation data with video timestamps by mapping
        DLC files to their corresponding video segments and applying the aligned
        timestamps from the video interfaces.

        Notes
        -----
        This method requires that video interfaces have already been aligned
        since it uses their timestamps for DLC alignment.
        """
        (
            epoch_name_to_dlc1_interfaces,
            epoch_name_to_dlc2_interfaces,
            epoch_name_to_video_interface,
        ) = self.get_epoch_name_mappings()
        if "DeepLabCut1" in self.data_interface_objects:
            for epoch_name, dlc1_interfaces in epoch_name_to_dlc1_interfaces.items():
                video_interface = epoch_name_to_video_interface[epoch_name]
                aligned_timestamps = video_interface.get_timestamps()
                for dlc_interface in dlc1_interfaces:
                    file_path = Path(dlc_interface.source_data["file_path"])
                    segment_number = file_path.name.split(").")[1].split("DLC")[0]
                    segment_index = int(segment_number) - 1
                    timestamps = aligned_timestamps[segment_index]
                    self.align_dlc_interface(timestamps, dlc_interface)
        if "DeepLabCut2" in self.data_interface_objects:
            for epoch_name, dlc2_interfaces in epoch_name_to_dlc2_interfaces.items():
                video_interface = epoch_name_to_video_interface[epoch_name]
                aligned_timestamps = video_interface.get_timestamps()
                for dlc_interface in dlc2_interfaces:
                    file_path = Path(dlc_interface.source_data["file_path"])
                    segment_number = file_path.name.split(").")[1].split("DLC")[0]
                    segment_index = int(segment_number) - 1
                    timestamps = aligned_timestamps[segment_index]
                    self.align_dlc_interface(timestamps, dlc_interface)

    def get_epoch_name_mappings(self):
        """Create mappings between epoch names and data interfaces.

        Analyzes file names to extract epoch names and creates dictionaries
        mapping epoch names to their corresponding DeepLabCut and video interfaces.
        This enables proper alignment of DLC data with video timestamps.

        Returns
        -------
        tuple
            A tuple containing three dictionaries mapping epoch names to interfaces.
        """
        epoch_name_to_dlc1_interfaces = {}
        if "DeepLabCut1" in self.data_interface_objects:
            for dlc_interface in self.data_interface_objects["DeepLabCut1"].dlc_interfaces:
                file_path = Path(dlc_interface.source_data["file_path"])
                epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_path.name)
                if epoch_name not in epoch_name_to_dlc1_interfaces:
                    epoch_name_to_dlc1_interfaces[epoch_name] = [dlc_interface]
                else:
                    epoch_name_to_dlc1_interfaces[epoch_name].append(dlc_interface)

        epoch_name_to_dlc2_interfaces = {}
        if "DeepLabCut2" in self.data_interface_objects:
            for dlc_interface in self.data_interface_objects["DeepLabCut2"].dlc_interfaces:
                file_path = Path(dlc_interface.source_data["file_path"])
                epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_path.name)
                if epoch_name not in epoch_name_to_dlc2_interfaces:
                    epoch_name_to_dlc2_interfaces[epoch_name] = [dlc_interface]
                else:
                    epoch_name_to_dlc2_interfaces[epoch_name].append(dlc_interface)

        epoch_name_to_video_interface = {}
        for video_interface in self.data_interface_objects["Video"].video_interfaces:
            file_path = Path(video_interface.source_data["file_paths"][0])
            epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_path.name)
            epoch_name_to_video_interface[epoch_name] = video_interface

        return epoch_name_to_dlc1_interfaces, epoch_name_to_dlc2_interfaces, epoch_name_to_video_interface

    def align_dlc_interface(self, aligned_timestamps: np.ndarray, dlc_interface):
        """Apply temporal alignment to a single DeepLabCut interface.

        Sets aligned timestamps for a DLC interface, handling potential mismatches
        between the number of pose estimation frames and video timestamps.

        Parameters
        ----------
        aligned_timestamps : np.ndarray
            Array of aligned timestamps for this DLC segment.
        dlc_interface : RiveraAndShukla2025DeepLabCutInterface
            The DLC interface to align.
        """
        file_path = Path(dlc_interface.source_data["file_path"])
        if ".h5" in file_path.suffixes:
            df = pd.read_hdf(file_path)
        elif ".csv" in file_path.suffixes:
            df = pd.read_csv(file_path, header=[0, 1, 2], index_col=0)
        if df.shape[0] != len(aligned_timestamps):
            msg = (
                f"Number of rows in the DLC file ({df.shape[0]}) does not match the number of aligned timestamps "
                f"({len(aligned_timestamps)})."
            )
            warnings.warn(msg)

            comment = (
                f"For epoch {file_path.name}, the number of rows in the DLC file ({df.shape[0]}) does not match "
                f"the number of aligned timestamps ({len(aligned_timestamps)}). As a result, the DLC timestamps were "
                f"set to be the first {df.shape[0]} video timestamps. This time interval should be treated with caution "
                f"with respect to the temporal alignment of the DLC data with other data streams."
            )
            start_time = aligned_timestamps[0]
            stop_time = aligned_timestamps[df.shape[0] - 1]
            self.dlc_timestamp_mismatches.append((start_time, stop_time, comment))

            aligned_timestamps = aligned_timestamps[: df.shape[0]]
        dlc_interface.set_aligned_timestamps(aligned_timestamps=aligned_timestamps)

    def add_invalid_intervals_to_nwbfile(
        self, clock_resets: list[int], dlc_timestamp_mismatches: list[tuple[float, float, str]], nwbfile: NWBFile
    ):
        """Add invalid intervals to NWB file based on detected clock resets.

        Marks intervals between epochs when a clock reset occurred as invalid in the NWB file
        to indicate periods of unreliable timing due to recording system resets.

        Parameters
        ----------
        clock_resets : list[int]
            List of indices where clock resets were detected. Each index corresponds to the video timestamps file path
            in the flattened list of all epochs and segments immediately following a clock reset.
        dlc_timestamp_mismatches : list[tuple[float, float, str]]
            List of epochs with DLC data that doesn't match video timestamps, tuple of (start_time, stop_time, comment).
        nwbfile : NWBFile
            The NWB file to which invalid intervals will be added.
        """
        if len(clock_resets) == 0 and len(dlc_timestamp_mismatches) == 0:
            return

        video_timestamps_file_paths = self.data_interface_objects["Video"].video_timestamps_file_paths
        flattened_file_paths = []
        for epoch_video_timestamps_file_paths in video_timestamps_file_paths:
            if not isinstance(epoch_video_timestamps_file_paths, list):
                epoch_video_timestamps_file_paths = [epoch_video_timestamps_file_paths]
            flattened_file_paths.extend(epoch_video_timestamps_file_paths)

        nwbfile.add_invalid_times_column(name="comment", description="Reason for invalid time interval")
        comment = (
            f"Between epochs (some time after start_time) the experimenter closed the program used to acquire data, "
            f"causing the clock to reset. As a result, the interval between epochs was approximated as "
            f"{self.INTER_EPOCH_INTERVAL} seconds. Due to the inherent uncertainty, this inter-epoch interval should be "
            f"considered invalid."
        )
        for clock_reset in clock_resets:
            last_file_path_pre_reset = Path(flattened_file_paths[clock_reset - 1])
            timestamps, _ = readCameraModuleTimeStamps(last_file_path_pre_reset)
            start_time = timestamps[-1]
            stop_time = start_time + self.INTER_EPOCH_INTERVAL
            nwbfile.add_invalid_time_interval(start_time=start_time, stop_time=stop_time, comment=comment)

        for start_time, stop_time, comment in dlc_timestamp_mismatches:
            nwbfile.add_invalid_time_interval(start_time=start_time, stop_time=stop_time, comment=comment)
