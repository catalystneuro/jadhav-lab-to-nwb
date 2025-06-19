"""Batch SpyGlass insertion script for Rivera and Shukla 2025 dataset.

This module provides functionality for inserting all converted NWB files from the
Rivera and Shukla 2025 social behavior dataset into a SpyGlass database. It handles
batch processing, database cleanup, and progress tracking for large-scale database
population operations.
"""

import datajoint as dj
from pathlib import Path
import sys
from tqdm import tqdm

dj_local_conf_path = "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_mock/dj_local_conf.json"
dj.config.load(dj_local_conf_path)  # load config for database connection info

# General Spyglass Imports
import spyglass.common as sgc  # this import connects to the database

# Custom Table Imports
sys.path.append(
    "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_extensions"
)
from task_leds import TaskLEDs

sys.path.append(
    "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/rivera_and_shukla_2025"
)
from rivera_and_shukla_2025_insert_session import insert_session


def main():
    """Insert all Rivera and Shukla 2025 NWB files into SpyGlass database.

    Performs batch insertion of all converted NWB files for the Rivera and Shukla 2025
    dataset. The function clears existing database entries, discovers all NWB files
    for the dataset subjects, and inserts them with progress tracking.

    The function suppresses logging and warnings for cleaner progress display.
    """
    # Suppress logging and warnings for cleaner progress bar
    import logging
    import warnings

    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")

    sgc.Nwbfile.delete()
    sgc.Task.delete()
    TaskLEDs.delete()
    spyglass_raw_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw")
    subject_ids = ["XFN1", "XFN2", "XFN3", "XFN4"]
    nwbfile_paths = []
    for subject_id in subject_ids:
        nwbfile_paths.extend(spyglass_raw_path.glob(f"sub-{subject_id}_ses-*.nwb"))
    nwbfile_paths = sorted(nwbfile_paths)
    for nwbfile_path in tqdm(nwbfile_paths, desc="Inserting sessions"):
        insert_session(nwbfile_path, rollback_on_fail=True, raise_err=True)


if __name__ == "__main__":
    main()
    print("Done!")
