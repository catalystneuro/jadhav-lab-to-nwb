"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import VideoInterface, DeepLabCutInterface

from jadhav_lab_to_nwb.olson_2024 import (
    Olson2024BehaviorInterface,
    Olson2024SpikeGadgetsRecordingInterface,
    Olson2024SortingInterface,
    Olson2024SpikeGadgetsLFPInterface,
)


class Olson2024NWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Recording=Olson2024SpikeGadgetsRecordingInterface,
        Sorting=Olson2024SortingInterface,
        LFP=Olson2024SpikeGadgetsLFPInterface,
        Video=VideoInterface,
        DeepLabCut=DeepLabCutInterface,
        Behavior=Olson2024BehaviorInterface,
    )
