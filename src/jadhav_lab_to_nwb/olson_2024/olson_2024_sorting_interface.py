"""Primary class for converting experiment-specific spike sorting."""
from pynwb.file import NWBFile
from pydantic import DirectoryPath
from pathlib import Path
import pandas as pd
from natsort import natsorted
from neuroconv.basedatainterface import BaseDataInterface


class Olson2024SortingInterface(BaseDataInterface):
    """Sorting interface for olson_2024 conversion"""

    keywords = ("extracellular electrophysiology", "spike sorting")

    def __init__(self, folder_path: DirectoryPath):
        super().__init__(folder_path=folder_path)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        folder_path = Path(self.source_data["folder_path"])
        nwbfile.add_unit_column(name="nTrode", description="The tetrode number for this unit")
        nwbfile.add_unit_column(name="unitInd", description="The integer id each unit within each nTrode")
        nwbfile.add_unit_column(
            name="global_id", description="The global id for each unit: nTrode{nTrode}_unit{unitInd}"
        )
        for file_path in folder_path.glob(r"*.txt"):
            if file_path.name.startswith("._"):
                continue
            nTrode = int(file_path.name.split("_")[0].split("nt")[1])
            df = pd.read_csv(file_path, names=["unitInd", "time"])
            unitInds = natsorted(df["unitInd"].unique())
            electrode_group = nwbfile.electrode_groups[f"nTrode{nTrode}"]
            for unitInd in unitInds:
                spike_times = df.time[df.unitInd == unitInd].to_numpy()
                nwbfile.add_unit(
                    spike_times=spike_times,
                    nTrode=nTrode,
                    unitInd=unitInd,
                    global_id=f"nTrode{nTrode}_unit{unitInd}",
                    electrode_group=electrode_group,
                )
