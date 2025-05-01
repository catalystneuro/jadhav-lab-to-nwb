"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter

from jadhav_lab_to_nwb.rivera_and_shukla_2025 import (
    RiveraAndShukla2025BehaviorInterface,
    RiveraAndShukla2025VideoInterface,
    RiveraAndShukla2025DeepLabCutInterface,
)
from jadhav_lab_to_nwb.olson_2024 import Olson2024DeepLabCutInterface


class RiveraAndShukla2025NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Video=RiveraAndShukla2025VideoInterface,
        Behavior=RiveraAndShukla2025BehaviorInterface,
        DeepLabCut=RiveraAndShukla2025DeepLabCutInterface,
    )
