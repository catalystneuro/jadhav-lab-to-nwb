"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    SpikeGadgetsRecordingInterface,
)

from jadhav_lab_to_nwb.olson_2024 import Olson2024BehaviorInterface


class Olson2024NWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        Recording=SpikeGadgetsRecordingInterface,
    )
