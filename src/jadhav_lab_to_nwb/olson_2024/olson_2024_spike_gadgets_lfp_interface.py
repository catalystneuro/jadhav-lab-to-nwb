"""Primary class for converting SpikeGadgets LFP data."""
from pynwb.file import NWBFile
from pathlib import Path
from pydantic import DirectoryPath
import numpy as np

from pynwb.ecephys import ElectricalSeries, LFP
from neuroconv import BaseDataInterface
from neuroconv.tools import nwb_helpers
from neuroconv.utils import get_base_schema

from .tools.spikegadgets import readTrodesExtractedDataFile


class Olson2024SpikeGadgetsLFPInterface(BaseDataInterface):
    """SpikeGadgets LFP interface for olson_2024 conversion"""

    keywords = ("lfp",)

    def __init__(self, folder_path: DirectoryPath):
        super().__init__(folder_path=folder_path)

    def get_metadata_schema(self):
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Ecephys"] = get_base_schema(tag="Ecephys")
        metadata_schema["properties"]["Ecephys"]["properties"]["LFP"] = {
            "type": "object",
            "required": ["ElectricalSeries"],
            "properties": {
                "ElectricalSeries": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "required": ["name", "description"],
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                        },
                    },
                },
            },
        }

        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, stub_test: bool = False):
        folder_path = Path(self.source_data["folder_path"])
        electrodes_table = nwbfile.electrodes.to_dataframe()
        lfp_data, lfp_electrodes, conversions = [], [], []
        for file_path in folder_path.glob("*.dat"):
            if file_path.name.startswith("._") or file_path.stem == "SL18_D19.timestamps":
                continue
            fieldsText = readTrodesExtractedDataFile(file_path)
            data = fieldsText["data"]
            conversion = float(fieldsText["voltage_scaling"]) * 1e-6
            channel_number = file_path.stem.split("ch")[-1]
            trode_number = file_path.stem.split("ch")[0].split("nt")[-1]
            chID = f"nTrode{trode_number}_elec{channel_number}"
            channel_index = electrodes_table.index[electrodes_table.chID == chID][0]
            assert electrodes_table.hasLFP[
                channel_index
            ], f"Channel {chID} has LFP data, but is not marked as an LFP channel."
            lfp_electrodes.append(channel_index)
            lfp_data.append(data)
            conversions.append(conversion)
        timestamp_file_path = folder_path / "SL18_D19.timestamps.dat"
        fieldsText = readTrodesExtractedDataFile(timestamp_file_path)
        timestamps = np.asarray(fieldsText["data"], dtype=np.float64)
        for conversion in conversions:
            assert conversion == conversions[0], "All LFP data must have the same conversion factor."
        conversion = conversions[0]
        lfp_data = np.array(lfp_data, dtype=np.int16).T
        lfp_table_region = nwbfile.create_electrode_table_region(
            region=lfp_electrodes,
            description="LFP electrodes",
        )
        if stub_test:
            lfp_data = lfp_data[:100]
            timestamps = timestamps[:100]
        lfp_metadata = metadata["Ecephys"]["LFP"]
        lfp_electrical_series = ElectricalSeries(
            name=lfp_metadata["ElectricalSeries"][0]["name"],
            description=lfp_metadata["ElectricalSeries"][0]["description"],
            data=lfp_data,
            timestamps=timestamps,
            electrodes=lfp_table_region,
            conversion=conversion,
        )
        lfp = LFP(electrical_series=lfp_electrical_series)
        ecephys_module = nwb_helpers.get_module(
            nwbfile,
            name="ecephys",
            description="Processed extracellular electrophysiology data.",
        )
        ecephys_module.add(lfp)
