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

    def __init__(self, folder_path: DirectoryPath, unit_stats_folder_path: DirectoryPath):
        super().__init__(folder_path=folder_path, unit_stats_folder_path=unit_stats_folder_path)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        folder_path = Path(self.source_data["folder_path"])
        unit_stats_folder_path = Path(self.source_data["unit_stats_folder_path"])
        nwbfile.add_unit_column(name="nTrode", description="The tetrode number for this unit")
        nwbfile.add_unit_column(name="unitInd", description="The integer id each unit within each nTrode")
        nwbfile.add_unit_column(
            name="global_id", description="The global id for each unit: nTrode{nTrode}_unit{unitInd}"
        )
        nwbfile.add_unit_column(name="nWaveforms", description="Number of waveforms (spikes) for each unit.")
        nwbfile.add_unit_column(
            name="waveformFWHM", description="Full width at half maximum of the template waveform in ms."
        )
        nwbfile.add_unit_column(
            name="waveformPeakMinusTrough", description="Peak minus trough of the template waveform in uV."
        )

        for file_path in folder_path.glob(r"*.txt"):
            if file_path.name.startswith("._"):
                continue
            unit_stats_file_name = file_path.name.split(".")[0] + ".unitexp.txt"
            unit_stats_file_path = unit_stats_folder_path / unit_stats_file_name
            names = pd.read_csv(unit_stats_file_path, nrows=0, header=0).columns
            unit_stats_df = pd.read_csv(unit_stats_file_path, skiprows=[0], header=None)
            unit_stats_df = unit_stats_df.iloc[:, : len(names)]
            unit_stats_df.columns = names
            nTrode = int(file_path.name.split("_")[0].split("nt")[1])
            df = pd.read_csv(file_path, names=["unitInd", "time"])
            unitInds = natsorted(df["unitInd"].unique())
            electrode_group = nwbfile.electrode_groups[f"nTrode{nTrode}"]
            for unitInd in unitInds:
                spike_times = df.time[df.unitInd == unitInd].to_numpy()
                unit_stats = unit_stats_df[unit_stats_df["Unit Number"] == unitInd]
                nWaveforms = unit_stats["Number of Waveforms"].iloc[0]
                waveformFWHM = unit_stats["Valley FWHM of Unit Template"].iloc[0]
                waveformPeakMinusTrough = unit_stats["Peak-Valley of Unit Template"].iloc[0]
                nwbfile.add_unit(
                    spike_times=spike_times,
                    electrode_group=electrode_group,
                    nTrode=nTrode,
                    unitInd=unitInd,
                    global_id=f"nTrode{nTrode}_unit{unitInd}",
                    nWaveforms=nWaveforms,
                    waveformFWHM=waveformFWHM,
                    waveformPeakMinusTrough=waveformPeakMinusTrough,
                )
