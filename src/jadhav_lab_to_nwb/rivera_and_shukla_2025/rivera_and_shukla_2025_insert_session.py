"""SpyGlass database insertion script for Rivera and Shukla 2025 dataset.

This module provides functions for inserting converted NWB files from the Rivera and
Shukla 2025 social behavior dataset into a SpyGlass database. It handles data ingestion,
custom table population, and validation testing for the database integration pipeline.
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

# Custom Table Imports
sys.path.append(
    "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_extensions"
)
from task_leds import TaskLEDs


def insert_task(nwbfile_path: Path):
    """Insert task-specific data from NWB file into SpyGlass custom tables.

    Populates custom TaskLEDs table with task-specific information extracted
    from the NWB file. This function handles the insertion of experimental
    task metadata that extends beyond standard SpyGlass tables.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the NWB file containing task data to be inserted.
        File must already be copied to SpyGlass raw data directory.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    TaskLEDs().make(key={"nwb_file_name": nwb_copy_file_name})


def insert_invalid_intervals(nwbfile_path: Path):
    """Insert invalid intervals from NWB file into SpyGlass IntervalList table.

    Populates the IntervalList table with invalid intervals extracted from the
    NWB file. This function ensures that periods of invalid data are properly
    recorded in the database for accurate analysis.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the NWB file containing invalid interval data to be inserted.
        File must already be copied to SpyGlass raw data directory.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        if nwbfile.invalid_times is None:
            return
        invalid_times_table = nwbfile.invalid_times.to_dataframe()

    inserts = invalid_times_table.apply(
        lambda row: {
            "nwb_file_name": nwb_copy_file_name,
            "interval_list_name": f"{row.tag}_invalid_intervals" if row.tag else f"invalid_intervals",
            "valid_times": np.asarray([[row.start_time, row.stop_time]]),
        },
        axis=1,
    ).tolist()

    sgc.IntervalList().insert(inserts, skip_duplicates=True)


def insert_session(nwbfile_path: Path, rollback_on_fail: bool = True, raise_err: bool = False):
    """Insert complete session data from NWB file into SpyGlass database.

    Performs comprehensive insertion of all session data including standard
    SpyGlass tables and custom task-specific tables. This is the main entry
    point for database ingestion of converted NWB files.

    Parameters
    ----------
    nwbfile_path : Path
        Path to the converted NWB file to insert into the database.
    rollback_on_fail : bool, optional
        Whether to rollback database transaction if insertion fails, by default True.
    raise_err : bool, optional
        Whether to raise exceptions on insertion errors, by default False.
    """
    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=rollback_on_fail, raise_err=raise_err)
    insert_task(nwbfile_path=nwbfile_path)
    insert_invalid_intervals(nwbfile_path=nwbfile_path)


def print_tables(nwbfile_path: Path):
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    with open("tables.txt", "w") as f:
        print("=== NWB File ===", file=f)
        print(sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== Session ===", file=f)
        print(sgc.Session & {"nwb_file_name": nwb_copy_file_name}, file=f)
        print("=== IntervalList ===", file=f)
        print(sgc.IntervalList(), file=f)
        print("=== Task ===", file=f)
        print(sgc.Task(), file=f)
        print("=== Task Epoch ===", file=f)
        print(sgc.TaskEpoch(), file=f)
        print("=== Task LEDs ===", file=f)
        print(TaskLEDs(), file=f)
        print("=== VideoFile ===", file=f)
        print(sgc.VideoFile & {"nwb_file_name": nwb_copy_file_name}, file=f)
        camera_names = (sgc.VideoFile & {"nwb_file_name": nwb_copy_file_name}).fetch("camera_name")
        print("=== CameraDevice ===", file=f)
        print(sgc.CameraDevice & [{"camera_name": camera_name} for camera_name in camera_names], file=f)


def test_behavior(nwbfile_path: Path):
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    time_series = (
        sgc.DIOEvents & {"nwb_file_name": nwb_copy_file_name, "dio_event_name": "matched_poke_A1"}
    ).fetch_nwb()[0]["dio"]
    spyglass_dio_timestamps = np.asarray(time_series.timestamps[:])
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        nwb_dio_timestamps = np.asarray(
            nwbfile.processing["behavior"]
            .data_interfaces["behavioral_events"]
            .time_series["matched_poke_A1"]
            .timestamps[:]
        )
    np.testing.assert_array_equal(spyglass_dio_timestamps, nwb_dio_timestamps)


def test_epoch(nwbfile_path: Path):
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    first_task_epoch = (sgc.TaskEpoch & {"nwb_file_name": nwb_copy_file_name, "epoch": 1}).fetch1()
    expected_first_task_epoch = {
        "nwb_file_name": "sub-XFN1_ses-07-20-2023-100_.nwb",
        "epoch": 1,
        "task_name": "SocialW_Left",
        "camera_name": None,
        "interval_list_name": "01",
        "task_environment": "left_Wmaze",
        "camera_names": [{"camera_name": "Track"}],
    }
    assert first_task_epoch == expected_first_task_epoch


def test_video(nwbfile_path: Path):
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    image_series = (sgc.VideoFile & {"nwb_file_name": nwb_copy_file_name, "epoch": 1}).fetch_nwb()[0]["video_file"]
    spyglass_external_file = image_series.external_file[0]
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        image_series = nwbfile.acquisition["Video_1-XFN1-XFN3"]
        nwb_external_file = image_series.external_file[0]
    assert (
        spyglass_external_file == nwb_external_file
    ), f"Spyglass external file: {spyglass_external_file}, NWB external file: {nwb_external_file}"


def test_invalid_intervals(nwbfile_path: Path):
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    invalid_intervals = (
        sgc.IntervalList & {"nwb_file_name": nwb_copy_file_name, "interval_list_name": "clock_reset_invalid_intervals"}
    ).fetch1("valid_times")
    expected_invalid_intervals = np.array([[8125.55, 9925.55]])
    np.testing.assert_array_equal(invalid_intervals, expected_invalid_intervals)


def main():
    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/sub-XFN1_ses-07-20-2023-100.nwb")
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)

    (sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}).delete()
    sgc.Task.delete()
    TaskLEDs.delete()

    insert_session(nwbfile_path, rollback_on_fail=True, raise_err=True)
    print_tables(nwbfile_path=nwbfile_path)

    test_behavior(nwbfile_path=nwbfile_path)
    test_epoch(nwbfile_path=nwbfile_path)
    test_video(nwbfile_path=nwbfile_path)
    test_invalid_intervals(nwbfile_path=nwbfile_path)


if __name__ == "__main__":
    main()
    print("Done!")
