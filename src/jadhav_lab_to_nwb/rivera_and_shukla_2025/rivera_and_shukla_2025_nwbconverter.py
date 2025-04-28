"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter

from jadhav_lab_to_nwb.rivera_and_shukla_2025 import (
    Olson2024BehaviorInterface,
    Olson2024VideoInterface,
    Olson2024DeepLabCutInterface,
    Olson2024SpikeGadgetsRecordingInterface,
    Olson2024SortingInterface,
    Olson2024SpikeGadgetsLFPInterface,
    Olson2024EpochInterface,
)


class RiveraAndShukla2025NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Recording=Olson2024SpikeGadgetsRecordingInterface,
        Sorting=Olson2024SortingInterface,
        LFP=Olson2024SpikeGadgetsLFPInterface,
        Video=Olson2024VideoInterface,
        DeepLabCut=Olson2024DeepLabCutInterface,
        Behavior=Olson2024BehaviorInterface,
        Epoch=Olson2024EpochInterface,
    )
