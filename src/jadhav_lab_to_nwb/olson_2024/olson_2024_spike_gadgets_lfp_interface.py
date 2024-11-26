"""Primary class for converting SpikeGadgets LFP data."""
from pynwb.file import NWBFile
from pathlib import Path
from pydantic import FilePath, DirectoryPath
import numpy as np
import re

from pynwb.ecephys import ElectricalSeries, LFP
from neuroconv import BaseDataInterface
from neuroconv.tools import nwb_helpers
from neuroconv.utils import get_base_schema


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


def readTrodesExtractedDataFile(filename: FilePath) -> dict:
    """Read Trodes Extracted Data File (.dat) and return as a dictionary.

    Adapted from https://docs.spikegadgets.com/en/latest/basic/ExportFunctions.html

    Parameters
    ----------
    filename : FilePath
        Path to the .dat file to read.

    Returns
    -------
    dict
        The contents of the .dat file as a dictionary
    """
    with open(filename, "rb") as f:
        # Check if first line is start of settings block
        if f.readline().decode("ascii").strip() != "<Start settings>":
            raise Exception("Settings format not supported")
        fields = True
        fieldsText = {}
        for line in f:
            # Read through block of settings
            if fields:
                line = line.decode("ascii").strip()
                # filling in fields dict
                if line != "<End settings>":
                    vals = line.split(": ")
                    fieldsText.update({vals[0].lower(): vals[1]})
                # End of settings block, signal end of fields
                else:
                    fields = False
                    dt = parseFields(fieldsText["fields"])
                    fieldsText["data"] = np.zeros([1], dtype=dt)
                    break
        # Reads rest of file at once, using dtype format generated by parseFields()
        dt = parseFields(fieldsText["fields"])
        data = np.fromfile(f, dt)
        fieldsText.update({"data": data})
        return fieldsText


def parseFields(fieldstr: str) -> np.dtype:
    """Parse the fields string from a Trodes Extracted Data File and return as a numpy dtype.

    Adapted from https://docs.spikegadgets.com/en/latest/basic/ExportFunctions.html

    Parameters
    ----------
    fieldstr : str
        The fields string from a Trodes Extracted Data File.

    Returns
    -------
    np.dtype
        The fields string as a numpy dtype.
    """
    # Returns np.dtype from field string
    sep = re.split("\s", re.sub(r"\>\<|\>|\<", " ", fieldstr).strip())
    # print(sep)
    typearr = []
    # Every two elmts is fieldname followed by datatype
    for i in range(0, sep.__len__(), 2):
        fieldname = sep[i]
        repeats = 1
        ftype = "uint32"
        # Finds if a <num>* is included in datatype
        if sep[i + 1].__contains__("*"):
            temptypes = re.split("\*", sep[i + 1])
            # Results in the correct assignment, whether str is num*dtype or dtype*num
            ftype = temptypes[temptypes[0].isdigit()]
            repeats = int(temptypes[temptypes[1].isdigit()])
        else:
            ftype = sep[i + 1]
        try:
            fieldtype = getattr(np, ftype)
        except AttributeError:
            print(ftype + " is not a valid field type.\n")
            exit(1)
        else:
            typearr.append((str(fieldname), fieldtype, repeats))
    return np.dtype(typearr)
