"""Primary class for converting SpikeGadgets Ephys Recordings."""
from pynwb.file import NWBFile
from pathlib import Path
from xml.etree import ElementTree
from pydantic import FilePath
import copy
from collections import Counter

from neuroconv.datainterfaces import SpikeGadgetsRecordingInterface
from neuroconv.utils import DeepDict
from spikeinterface.extractors import SpikeGadgetsRecordingExtractor


class Olson2024SpikeGadgetsRecordingInterface(SpikeGadgetsRecordingInterface):
    """SpikeGadgets RecordingInterface for olson_2024 conversion."""

    Extractor = SpikeGadgetsRecordingExtractor

    def __init__(self, file_path: FilePath, **kwargs):
        super().__init__(file_path=file_path, **kwargs)

        header_txt = get_spikegadgets_header(file_path)
        root = ElementTree.fromstring(header_txt)
        sconf = root.find("SpikeConfiguration")
        self.hwChan_to_nTrode, self.hwChan_to_hasLFP = {}, {}
        for tetrode in sconf.findall("SpikeNTrode"):
            nTrode = tetrode.attrib["id"]
            lfp_chan = int(tetrode.attrib["LFPChan"])
            for i, electrode in enumerate(tetrode.findall("SpikeChannel")):
                hwChan = electrode.attrib["hwChan"]
                hasLFP = lfp_chan == i + 1
                self.hwChan_to_nTrode[hwChan] = nTrode
                self.hwChan_to_hasLFP[hwChan] = hasLFP
        self.nTrode_to_hwChans = {nTrode: [] for nTrode in self.hwChan_to_nTrode.values()}
        for hwChan, nTrode in self.hwChan_to_nTrode.items():
            self.nTrode_to_hwChans[nTrode].append(hwChan)

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Ecephys"]["properties"]["TrodeGroups"] = {
            "type": "array",
            "minItems": 1,
            "items": {
                "required": ["name", "location", "device", "nTrodes"],
                "properties": {
                    "name": {"description": "the name of this Trode group", "pattern": "^[^/]*$", "type": "string"},
                    "location": {"description": "description of location of this Trode group", "type": "string"},
                    "device": {
                        "description": "the device that was used to record from this Trode group",
                        "type": "string",
                        "target": "pynwb.device.Device",
                    },
                    "nTrodes": {
                        "description": "the tetrode numbers that belong to this Trode group",
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                    "position": {
                        "description": "stereotaxic position of this electrode group (x, y, z)",
                        "type": "array",
                    },
                },
                "type": "object",
                "additionalProperties": False,
                "tag": "pynwb.ecephys.ElectrodeGroup",
            },
        }
        return metadata_schema

    def reformat_metadata(self, metadata: dict) -> dict:
        TrodeGroups = metadata["Ecephys"]["TrodeGroups"]
        metadata["Ecephys"]["ElectrodeGroup"] = []
        for group in TrodeGroups:
            nTrodes = group.pop("nTrodes")
            for nTrode in nTrodes:
                electrode_group = copy.deepcopy(group)
                electrode_group["name"] = f"nTrode{nTrode}"
                electrode_group["description"] = f"ElectrodeGroup for tetrode {nTrode}"
                metadata["Ecephys"]["ElectrodeGroup"].append(electrode_group)
        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, **conversion_options):
        metadata = self.reformat_metadata(metadata)
        channel_ids = self.recording_extractor.get_channel_ids()
        channel_names = self.recording_extractor.get_property(key="channel_name", ids=channel_ids)
        group_names, chIDs, hasLFPs, locations = [], [], [], []
        for channel_name in channel_names:
            hwChan = channel_name.split("hwChan")[-1]
            nTrode = self.hwChan_to_nTrode[hwChan]
            hasLFP = self.hwChan_to_hasLFP[hwChan]
            electrode_group = next(
                group for group in metadata["Ecephys"]["ElectrodeGroup"] if group["name"] == f"nTrode{nTrode}"
            )
            location = electrode_group["location"]
            trode_chan = self.nTrode_to_hwChans[nTrode].index(hwChan) + 1

            group_names.append(f"nTrode{nTrode}")
            hasLFPs.append(hasLFP)
            locations.append(location)
            chIDs.append(f"nTrode{nTrode}_elec{trode_chan}")

        self.recording_extractor.set_property(key="group_name", ids=channel_ids, values=group_names)
        self.recording_extractor.set_property(key="chID", ids=channel_ids, values=chIDs)
        self.recording_extractor.set_property(key="hasLFP", ids=channel_ids, values=hasLFPs)
        self.recording_extractor.set_property(
            key="brain_area", ids=channel_ids, values=locations
        )  # brain_area in spikeinterface is location in nwb

        super().add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, **conversion_options)


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
