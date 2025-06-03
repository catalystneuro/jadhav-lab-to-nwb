"""NWB converter for Olson 2024 dataset.

This module provides the main NWB converter class for the Olson 2024
electrophysiology dataset. It orchestrates the conversion of multiple data
modalities including electrophysiology, behavior, video, and pose estimation
data into a unified NWB file format.
"""
from datetime import datetime
from pathlib import Path
from neuroconv import NWBConverter

from jadhav_lab_to_nwb.olson_2024 import (
    Olson2024BehaviorInterface,
    Olson2024VideoInterface,
    Olson2024DeepLabCutInterface,
    Olson2024SpikeGadgetsRecordingInterface,
    Olson2024SortingInterface,
    Olson2024SpikeGadgetsLFPInterface,
    Olson2024EpochInterface,
)

from ..tools.spikegadgets import readCameraModuleTimeStamps


class Olson2024NWBConverter(NWBConverter):
    """Main NWB converter for Olson 2024 electrophysiology dataset.

    This converter orchestrates the integration of multiple data modalities from
    the Olson 2024 experiments into a unified NWB file. It handles temporal
    alignment between video, pose estimation, electrophysiology, and behavioral
    data streams to ensure proper synchronization across all recorded modalities.
    """

    data_interface_classes = dict(
        Recording=Olson2024SpikeGadgetsRecordingInterface,
        Sorting=Olson2024SortingInterface,
        LFP=Olson2024SpikeGadgetsLFPInterface,
        Video=Olson2024VideoInterface,
        DeepLabCut=Olson2024DeepLabCutInterface,
        Behavior=Olson2024BehaviorInterface,
        Epoch=Olson2024EpochInterface,
    )

    def temporally_align_data_interfaces(self, metadata: dict | None = None, conversion_options: dict | None = None):
        """Temporally align video and pose estimation data interfaces.

        Reads camera module timestamps from SpikeGadgets system and applies them
        to both video and DeepLabCut interfaces to ensure temporal synchronization
        between behavioral video recordings and pose estimation data.

        Parameters
        ----------
        metadata : dict, optional
            Metadata dictionary (not used in current implementation).
        conversion_options : dict, optional
            Conversion options dictionary (not used in current implementation).
        """
        video_timestamps_file_paths = self.data_interface_objects["Video"].video_timestamps_file_paths

        # Align interface timestamps
        video_interfaces = self.data_interface_objects["Video"].video_interfaces
        dlc_interfaces = self.data_interface_objects["DeepLabCut"].dlc_interfaces
        for video_timestamps_file_path, video_interface, dlc_interface in zip(
            video_timestamps_file_paths, video_interfaces, dlc_interfaces
        ):
            timestamps, clock_rate = readCameraModuleTimeStamps(video_timestamps_file_path)
            video_interface.set_aligned_timestamps(aligned_timestamps=[timestamps])
            dlc_interface.set_aligned_timestamps(aligned_timestamps=timestamps)
