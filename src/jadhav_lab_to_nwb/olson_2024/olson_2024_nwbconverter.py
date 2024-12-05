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

    def temporally_align_data_interfaces(self):
        first_video_interface = self.data_interface_objects["Video"].video_interfaces[0]
        first_epoch_folder_name = first_video_interface.source_data["file_paths"][0].parent.name
        first_start_datetime = get_start_datetime(first_epoch_folder_name)
        for video_interface in self.data_interface_objects["Video"].video_interfaces:
            epoch_folder_name = video_interface.source_data["file_paths"][0].parent.name
            start_datetime = get_start_datetime(epoch_folder_name)
            start_time = (start_datetime - first_start_datetime).total_seconds()
            video_interface.set_aligned_segment_starting_times(aligned_segment_starting_times=[start_time])


def get_start_datetime(epoch_folder_name: str) -> datetime:
    """Get the start datetime of the epoch from the folder name.

    Parameters
    ----------
    epoch_folder_path : pathlib.Path
        The path to the epoch folder.

    Returns
    -------
    datetime.datetime
        The start datetime of the epoch.
    """
    split_name = epoch_folder_name.split("_")
    start_datetime = datetime.strptime(split_name[-2] + "_" + split_name[-1], "%Y%m%d_%H%M%S")
    return start_datetime
