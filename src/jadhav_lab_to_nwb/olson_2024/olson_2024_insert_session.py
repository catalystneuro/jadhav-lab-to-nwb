"""SpyGlass database insertion script for Olson 2024 dataset.

This module provides functionality for inserting converted NWB files from the
Olson 2024 dataset into a SpyGlass database. It handles the complete ingestion
workflow including electrophysiology, behavior, video, spike sorting, and custom
task data, along with testing to verify data integrity.
"""

from pynwb import NWBHDF5IO
import numpy as np
import datajoint as dj
from pathlib import Path
import sys

dj_local_conf_path = "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_mock/dj_local_conf.json"
dj.config.load(dj_local_conf_path)  # load config for database connection info

# General Spyglass Imports
import spyglass.common as sgc  # this import connects to the database
import spyglass.data_import as sgi
from spyglass.utils.nwb_helper_fn import get_nwb_copy_filename

# Spike Sorting Imports
from spyglass.spikesorting.spikesorting_merge import SpikeSortingOutput
import spyglass.spikesorting.v1 as sgs
from spyglass.spikesorting.analysis.v1.group import SortedSpikesGroup
from spyglass.spikesorting.analysis.v1.group import UnitSelectionParams
from spyglass.spikesorting.analysis.v1.unit_annotation import UnitAnnotation

# Custom Table Imports
sys.path.append(
    "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_extensions"
)
from task_leds import TaskLEDs

# LFP Imports
import spyglass.lfp as sglfp
from spyglass.utils.nwb_helper_fn import estimate_sampling_rate
from pynwb.ecephys import ElectricalSeries, LFP

from tqdm import tqdm


def insert_sorting(nwbfile_path: Path):
    """Insert spike sorting data and unit annotations into SpyGlass database.

    Creates a sorted spikes group containing all units and adds detailed unit
    annotations including tetrode information, waveform statistics, and unit
    identifiers. Annotations are categorized as either labels (categorical)
    or quantifications (numerical) based on their data type.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the NWB file containing spike sorting results and unit metadata.

    Notes
    -----
    The function creates the following annotations:
    - Labels: nTrode, unitInd, globalID
    - Quantifications: nWaveforms, waveformFWHM, waveformPeakMinusTrough
    """
    io = NWBHDF5IO(nwbfile_path, "r")
    nwbfile = io.read()
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    merge_id = str((SpikeSortingOutput.ImportedSpikeSorting & {"nwb_file_name": nwb_copy_file_name}).fetch1("merge_id"))

    UnitSelectionParams().insert_default()
    group_name = "all_units"
    SortedSpikesGroup().create_group(
        group_name=group_name,
        nwb_file_name=nwb_copy_file_name,
        keys=[{"spikesorting_merge_id": merge_id}],
    )
    annotation_to_type = {
        "nTrode": "label",
        "unitInd": "label",
        "globalID": "label",
        "nWaveforms": "quantification",
        "waveformFWHM": "quantification",
        "waveformPeakMinusTrough": "quantification",
    }
    group_key = {
        "nwb_file_name": nwb_copy_file_name,
        "sorted_spikes_group_name": group_name,
    }
    group_key = (SortedSpikesGroup & group_key).fetch1("KEY")
    _, unit_ids = SortedSpikesGroup().fetch_spike_data(group_key, return_unit_ids=True)

    for unit_key in tqdm(unit_ids, desc="Inserting Unit Annotations"):
        unit_id = unit_key["unit_id"]
        for annotation, annotation_type in annotation_to_type.items():
            annotation_value = nwbfile.units.get((unit_id, annotation))
            annotation_key = {
                **unit_key,
                "annotation": annotation,
                annotation_type: annotation_value,
            }
            UnitAnnotation().add_annotation(annotation_key, skip_duplicates=True)
    io.close()


def insert_task(nwbfile_path: Path):
    """Insert custom task LED data into SpyGlass database.

    Processes task-specific LED behavioral data using the custom TaskLEDs
    extension table. This handles experiment-specific behavioral markers
    and task events that are not part of standard SpyGlass tables.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the NWB file containing task and behavioral data.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    TaskLEDs().make(key={"nwb_file_name": nwb_copy_file_name})


def insert_session(nwbfile_path: Path, rollback_on_fail: bool = True, raise_err: bool = False):
    """Insert complete experimental session data into SpyGlass database.

    Orchestrates the full insertion workflow for an NWB file including standard
    SpyGlass session data (ephys, behavior, video, LFP) and custom extensions
    (spike sorting annotations, task LEDs). This is the main entry point for
    database ingestion.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the converted NWB file to insert into the database.
    rollback_on_fail : bool, optional
        Whether to rollback database transaction if any insertion fails.
        Default is True for data integrity.
    raise_err : bool, optional
        Whether to raise exceptions on insertion errors. Default is False
        to allow graceful error handling.
    """
    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=rollback_on_fail, raise_err=raise_err)
    insert_sorting(nwbfile_path=nwbfile_path)
    insert_task(nwbfile_path=nwbfile_path)


def print_tables(nwbfile_path: Path):
    """Print database table contents for debugging and verification.

    Outputs the contents of all relevant SpyGlass tables to a text file
    for inspection and debugging purposes. Useful for verifying that
    data was inserted correctly.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the NWB file that was inserted into the database.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    with open("tables.txt", "w") as f:
        print("=== NWB File ===", file=f)
        print(sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== Session ===", file=f)
        print(sgc.Session & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== DIOEvents ===", file=f)
        print(sgc.DIOEvents & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== Electrode ===", file=f)
        print(sgc.Electrode & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== Electrode Group ===", file=f)
        print(sgc.ElectrodeGroup & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== Probe ===", file=f)
        print(sgc.Probe & {"probe_id": "my_probe_type"}, file=f)
        print("=== Probe Shank ===", file=f)
        print(sgc.Probe.Shank & {"probe_id": "my_probe_type"}, file=f)
        print("=== Probe Electrode ===", file=f)
        print(sgc.Probe.Electrode & {"probe_id": "my_probe_type"}, file=f)
        print("=== Raw ===", file=f)
        print(sgc.Raw & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== DataAcquisitionDevice ===", file=f)
        print(sgc.DataAcquisitionDevice & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== IntervalList ===", file=f)
        print(sgc.IntervalList(), file=f)
        print("=== Task ===", file=f)
        print(sgc.Task(), file=f)
        print("=== Task Epoch ===", file=f)
        print(sgc.TaskEpoch(), file=f)
        print("=== Task LEDs ===", file=f)
        print(TaskLEDs(), file=f)
        print("=== AnalysisNwbfile ===", file=f)
        print(sgc.AnalysisNwbfile & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== LFPElectrodeGroup ===", file=f)
        print(sglfp.lfp_electrode.LFPElectrodeGroup & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== ImportedLFP ===", file=f)
        print(sglfp.ImportedLFP & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== LFPOutput ===", file=f)
        print(sglfp.lfp_merge.LFPOutput & {"nwb_file_name": nwb_copy_file_name}, file=f)
        merge_id = str(
            (SpikeSortingOutput.ImportedSpikeSorting & {"nwb_file_name": nwb_copy_file_name}).fetch1("merge_id")
        )
        print("=== Unit Annotation ===", file=f)
        print(UnitAnnotation().Annotation & {"spike_sorting_merge_id": merge_id}, file=f)
        print("=== VideoFile ===", file=f)
        print(sgc.VideoFile & {"nwb_file_name": nwb_copy_file_name}, file=f)
        camera_names = (sgc.VideoFile & {"nwb_file_name": nwb_copy_file_name}).fetch("camera_name")
        print("=== CameraDevice ===", file=f)
        print(sgc.CameraDevice & [{"camera_name": camera_name} for camera_name in camera_names], file=f)


def test_behavior(nwbfile_path: Path):
    """Test behavioral data integrity between NWB file and SpyGlass database.

    Verifies that DIO event data was correctly inserted by comparing the first
    100 data points of reward_well_1 events between the original NWB file and
    the SpyGlass database.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the original NWB file for comparison.

    Raises
    ------
    AssertionError
        If data arrays do not match between NWB and SpyGlass.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    time_series = (
        sgc.DIOEvents & {"nwb_file_name": nwb_copy_file_name, "dio_event_name": "reward_well_1"}
    ).fetch_nwb()[0]["dio"]
    spyglass_dio_data = np.asarray(time_series.data[:100])
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        nwb_dio_data = np.asarray(
            nwbfile.processing["behavior"].data_interfaces["behavioral_events"].time_series["reward_well_1"].data[:100]
        )
    np.testing.assert_array_equal(spyglass_dio_data, nwb_dio_data)


def test_ephys(nwbfile_path: Path):
    """Test electrophysiology data integrity between NWB file and SpyGlass database.

    Verifies that raw electrical series data was correctly inserted by comparing
    the first 100 data points between the original NWB file and SpyGlass database.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the original NWB file for comparison.

    Raises
    ------
    AssertionError
        If data arrays do not match between NWB and SpyGlass.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    electrical_series = (sgc.Raw & {"nwb_file_name": nwb_copy_file_name}).fetch_nwb()[0]["raw"]
    spyglass_raw_data = np.asarray(electrical_series.data[:100])
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        nwb_raw_data = np.asarray(nwbfile.acquisition["ElectricalSeries"].data[:100])
    np.testing.assert_array_equal(spyglass_raw_data, nwb_raw_data)


def test_epoch(nwbfile_path: Path):
    """Test epoch data integrity between NWB file and SpyGlass database.

    Verifies that task epoch information was correctly inserted by comparing
    the first task epoch metadata between expected values and database contents.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the original NWB file for comparison.

    Raises
    ------
    AssertionError
        If epoch metadata does not match expected values.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    first_task_epoch = (sgc.TaskEpoch & {"nwb_file_name": nwb_copy_file_name, "epoch": 1}).fetch1()
    expected_first_task_epoch = {
        "nwb_file_name": nwb_copy_file_name,
        "epoch": 1,
        "task_name": "Sleep",
        "camera_name": None,
        "interval_list_name": "01",
        "task_environment": "SLP",
        "camera_names": [{"camera_name": "SleepBox"}],
    }
    assert first_task_epoch == expected_first_task_epoch


def test_lfp(nwbfile_path: Path):
    """Test LFP data integrity between NWB file and SpyGlass database.

    Verifies that local field potential data was correctly inserted by comparing
    the first 100 data points between the original NWB file and SpyGlass database.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the original NWB file for comparison.

    Raises
    ------
    AssertionError
        If data arrays do not match between NWB and SpyGlass.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    lfp_electrical_series = (sglfp.ImportedLFP & {"nwb_file_name": nwb_copy_file_name}).fetch_nwb()[0]["lfp"]
    spyglass_lfp_data = np.asarray(lfp_electrical_series.data[:100])
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        nwb_lfp_data = np.asarray(
            nwbfile.processing["ecephys"]["LFP"].electrical_series["ElectricalSeriesLFP"].data[:100]
        )
    np.testing.assert_array_equal(spyglass_lfp_data, nwb_lfp_data)


def test_sorting(nwbfile_path: Path):
    """Test spike sorting data integrity between NWB file and SpyGlass database.

    Verifies that spike times for all units were correctly inserted by comparing
    spike time arrays between the original NWB file and SpyGlass database.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the original NWB file for comparison.

    Raises
    ------
    AssertionError
        If spike time arrays do not match between NWB and SpyGlass.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        units_table = nwbfile.units.to_dataframe()
    group_key = {
        "nwb_file_name": nwb_copy_file_name,
        "sorted_spikes_group_name": "all_units",
    }
    group_key = (SortedSpikesGroup & group_key).fetch1("KEY")
    spikes_spyglass = SortedSpikesGroup().fetch_spike_data(group_key)
    spikes_nwb = [unit.spike_times for _, unit in units_table.iterrows()]
    for nwb_unit, spyglass_unit in zip(spikes_nwb, spikes_spyglass):
        np.testing.assert_array_equal(nwb_unit, spyglass_unit)


def test_video(nwbfile_path: Path):
    """Test video data integrity between NWB file and SpyGlass database.

    Verifies that video file references were correctly inserted by comparing
    external file paths between the original NWB file and SpyGlass database.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the original NWB file for comparison.

    Raises
    ------
    AssertionError
        If external file paths do not match between NWB and SpyGlass.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    image_series = (sgc.VideoFile & {"nwb_file_name": nwb_copy_file_name}).fetch_nwb()[0]["video_file"]
    spyglass_external_file = image_series.external_file[0]
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        image_series = nwbfile.acquisition["Video_S01_F01_BOX_SLP"]
        nwb_external_file = image_series.external_file[0]
    assert spyglass_external_file == nwb_external_file


def main():
    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/sub-SL18_ses-D19.nwb")
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)

    (sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}).delete()
    sgc.ProbeType.delete()
    sgc.DataAcquisitionDevice.delete()
    sgc.Task.delete()

    insert_session(nwbfile_path, rollback_on_fail=True, raise_err=True)
    print_tables(nwbfile_path=nwbfile_path)

    test_behavior(nwbfile_path=nwbfile_path)
    test_ephys(nwbfile_path=nwbfile_path)
    test_epoch(nwbfile_path=nwbfile_path)
    test_lfp(nwbfile_path=nwbfile_path)
    test_sorting(nwbfile_path=nwbfile_path)
    test_video(nwbfile_path=nwbfile_path)


if __name__ == "__main__":
    main()
    print("Done!")
