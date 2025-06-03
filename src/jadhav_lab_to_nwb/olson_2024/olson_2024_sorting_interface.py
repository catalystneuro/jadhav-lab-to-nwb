"""Spike sorting interface for Olson 2024 dataset conversion.

This module provides the spike sorting data interface for converting spike sorting
results from the Olson 2024 electrophysiology dataset. It handles spike times
and unit statistics from tetrode recordings and converts them to NWB format.
"""
from pynwb.file import NWBFile
from pydantic import DirectoryPath
from pathlib import Path
import pandas as pd
from natsort import natsorted
from neuroconv.basedatainterface import BaseDataInterface


class Olson2024SortingInterface(BaseDataInterface):
    """Data interface for converting Olson 2024 spike sorting data to NWB format.

    This interface handles spike sorting results from tetrode recordings,
    including spike times and unit statistics. It processes data from multiple
    tetrodes and adds units with comprehensive metadata to the NWB file.
    """

    keywords = ("extracellular electrophysiology", "spike sorting")

    def __init__(self, spike_times_folder_path: DirectoryPath, unit_stats_folder_path: DirectoryPath):
        """Initialize the Olson 2024 spike sorting interface.

        Parameters
        ----------
        spike_times_folder_path : DirectoryPath
            Path to directory containing spike times files (.txt). Each file contains
            spike times for units from a single tetrode with columns: unitInd, time.
        unit_stats_folder_path : DirectoryPath
            Path to directory containing unit statistics files (.unitexp.txt). Each file
            contains waveform statistics and quality metrics for units from a tetrode.
        """
        super().__init__(spike_times_folder_path=spike_times_folder_path, unit_stats_folder_path=unit_stats_folder_path)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        """Add spike sorting data to the NWB file.

        Processes spike times and unit statistics files to add units with comprehensive
        metadata to the NWB file. Creates custom unit columns for tetrode-specific
        information and waveform characteristics.

        Parameters
        ----------
        nwbfile : NWBFile
            The NWB file object to add spike sorting data to.
        metadata : dict
            Metadata dictionary (not used in current implementation).
        """
        spike_times_folder_path = Path(self.source_data["spike_times_folder_path"])
        unit_stats_folder_path = Path(self.source_data["unit_stats_folder_path"])
        nwbfile.add_unit_column(name="nTrode", description="The tetrode number for this unit")
        nwbfile.add_unit_column(name="unitInd", description="The integer id each unit within each nTrode")
        nwbfile.add_unit_column(
            name="globalID", description="The global id for each unit: nTrode{nTrode}_unit{unitInd}"
        )
        nwbfile.add_unit_column(name="nWaveforms", description="Number of waveforms (spikes) for each unit.")
        nwbfile.add_unit_column(
            name="waveformFWHM", description="Full width at half maximum of the template waveform in ms."
        )
        nwbfile.add_unit_column(
            name="waveformPeakMinusTrough", description="Peak minus trough of the template waveform in uV."
        )

        for file_path in spike_times_folder_path.glob(r"*.txt"):
            if file_path.name.startswith("._"):
                continue
            unit_stats_file_name = file_path.name.split(".")[0] + ".unitexp.txt"
            unit_stats_file_path = unit_stats_folder_path / unit_stats_file_name
            names = pd.read_csv(unit_stats_file_path, nrows=0, header=0).columns
            unit_stats_df = pd.read_csv(unit_stats_file_path, skiprows=[0], header=None)
            unit_stats_df = unit_stats_df.iloc[:, : len(names)]
            unit_stats_df.columns = names
            nTrode = int(file_path.name.split("_")[0].split("nt")[1])
            spike_times_df = pd.read_csv(file_path, names=["unitInd", "time"])
            unitInds = natsorted(spike_times_df["unitInd"].unique())
            electrode_group = nwbfile.electrode_groups[f"nTrode{nTrode}"]
            for unitInd in unitInds:
                spike_times = spike_times_df.time[spike_times_df.unitInd == unitInd].to_numpy()
                unit_stats = unit_stats_df[unit_stats_df["Unit Number"] == unitInd]
                nWaveforms = unit_stats["Number of Waveforms"].iloc[0]
                waveformFWHM = unit_stats["Valley FWHM of Unit Template"].iloc[0]
                waveformPeakMinusTrough = unit_stats["Peak-Valley of Unit Template"].iloc[0]
                nwbfile.add_unit(
                    spike_times=spike_times,
                    electrode_group=electrode_group,
                    nTrode=nTrode,
                    unitInd=unitInd,
                    globalID=f"nTrode{nTrode}_unit{unitInd}",
                    nWaveforms=nWaveforms,
                    waveformFWHM=waveformFWHM,
                    waveformPeakMinusTrough=waveformPeakMinusTrough,
                )
