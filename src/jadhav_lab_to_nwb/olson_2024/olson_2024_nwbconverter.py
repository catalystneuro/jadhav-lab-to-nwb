"""Primary NWBConverter class for this dataset."""
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

from ..common.tools.spikegadgets import readCameraModuleTimeStamps


class Olson2024NWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

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
        video_timestamps_file_paths = self.data_interface_objects["Video"].video_timestamps_file_paths

        # Align interface timestamps
        video_interfaces = self.data_interface_objects["Video"].video_interfaces
        for video_timestamps_file_path, video_interface in zip(video_timestamps_file_paths, video_interfaces):
            timestamps, clock_rate = readCameraModuleTimeStamps(video_timestamps_file_path)
            video_interface.set_aligned_timestamps(aligned_timestamps=[timestamps])
