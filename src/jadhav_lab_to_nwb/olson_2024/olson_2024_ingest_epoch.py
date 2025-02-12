"""Ingest epoch/task data from a converted NWB file into a spyglass database."""

import numpy as np
from pynwb import NWBHDF5IO
import datajoint as dj
from pathlib import Path

dj_local_conf_path = "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_mock/dj_local_conf.json"
dj.config.load(dj_local_conf_path)  # load config for database connection info

# spyglass.common has the most frequently used tables
import spyglass.common as sgc  # this import connects to the database

# spyglass.data_import has tools for inserting NWB files into the database
import spyglass.data_import as sgi
from spyglass.utils.nwb_helper_fn import get_nwb_copy_filename

# Spike Sorting
from spyglass.spikesorting.spikesorting_merge import SpikeSortingOutput
import spyglass.spikesorting.v1 as sgs
from spyglass.spikesorting.analysis.v1.group import SortedSpikesGroup

# Custom tables
import sys

sys.path.append(
    "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/olson_2024/spyglass_extensions"
)
from epoch import TaskLEDs


def main():
    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/sub-SL18_ses-D19.nwb")
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)

    if sgc.Session & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Session & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}).delete()
    sgc.ProbeType.delete()
    if sgc.DIOEvents & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.DIOEvents & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.IntervalList & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.IntervalList & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.Task():
        sgc.Task.delete()
    if sgc.TaskEpoch():
        sgc.TaskEpoch.delete()
    if TaskLEDs():
        TaskLEDs().delete()

    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=True, raise_err=True)
    TaskLEDs().make(key={"nwb_file_name": nwb_copy_file_name})
    print("=== Session ===")
    print(sgc.Session & {"nwb_file_name": nwb_copy_file_name})
    print("=== NWB File ===")
    print(sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name})
    print("=== IntervalList ===")
    print(sgc.IntervalList())
    print("=== Task ===")
    print(sgc.Task())
    print("=== Task Epoch ===")
    print(sgc.TaskEpoch())
    print("=== Task LEDs ===")
    print(TaskLEDs())


if __name__ == "__main__":
    main()
    print("Done!")
