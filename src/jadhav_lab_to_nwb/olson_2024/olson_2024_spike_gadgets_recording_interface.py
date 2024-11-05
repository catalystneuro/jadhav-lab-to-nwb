"""Primary class for converting SpikeGadgets Ephys Recordings."""
from pynwb.file import NWBFile
from pathlib import Path
from xml.etree import ElementTree

from neuroconv.datainterfaces import SpikeGadgetsRecordingInterface
from neuroconv.utils import DeepDict
from spikeinterface.extractors import SpikeGadgetsRecordingExtractor


class Olson2024SpikeGadgetsRecordingInterface(SpikeGadgetsRecordingInterface):
    """SpikeGadgets RecordingInterface for olson_2024 conversion."""

    Extractor = SpikeGadgetsRecordingExtractor

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        channel_ids = self.recording_extractor.get_channel_ids()
        channel_names = self.recording_extractor.get_property(key="channel_name", ids=channel_ids)
        header = get_spikegadgets_header(self.source_data["file_path"])
        hwChan_to_nTrode = extract_hwChan_to_nTrode(header)
        group_names = []
        for channel_name in channel_names:
            hwChan = channel_name.split("hwChan")[-1]
            nTrode = hwChan_to_nTrode[hwChan]
            group_names.append(f"nTrode{nTrode}")
        self.recording_extractor.set_property(key="group_name", ids=channel_ids, values=group_names)

        return metadata


def get_spikegadgets_header(file_path: str | Path):
    """Get the header information from a SpikeGadgets .rec file.

    This function reads the .rec file until the "</Configuration>" tag to extract the header information.

    Parameters
    ----------
    file_path : str | Path
        Path to the .rec file.

    Returns
    -------
    str
        The header information from the .rec file.

    Raises
    ------
    ValueError
        If the header does not contain "</Configuration>".
    """
    header_size = None
    with open(file_path, mode="rb") as f:
        while True:
            line = f.readline()
            if b"</Configuration>" in line:
                header_size = f.tell()
                break

        if header_size is None:
            ValueError("SpikeGadgets: the xml header does not contain '</Configuration>'")

        f.seek(0)
        return f.read(header_size).decode("utf8")


def extract_hwChan_to_nTrode(header_txt):
    """Extract the hardware channel to tetrode mapping from the header text.

    Parameters
    ----------
    header_txt : str
        The header text.

    Returns
    -------
    dict
        A dictionary mapping hardware channel IDs to tetrode IDs.
    """
    root = ElementTree.fromstring(header_txt)
    sconf = root.find("SpikeConfiguration")
    hwChan_to_nTrode = dict()
    for tetrode in sconf.findall("SpikeNTrode"):
        nTrode = tetrode.attrib["id"]
        for electrode in tetrode.findall("SpikeChannel"):
            hwChan = electrode.attrib["hwChan"]
            hwChan_to_nTrode[hwChan] = nTrode
    return hwChan_to_nTrode
