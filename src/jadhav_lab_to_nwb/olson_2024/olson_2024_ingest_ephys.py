"""Ingest ephys data from a converted NWB file into a spyglass database."""

from pynwb import NWBHDF5IO
import numpy as np
import datajoint as dj
from pathlib import Path

dj_local_conf_path = "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_mock/dj_local_conf.json"
dj.config.load(dj_local_conf_path)  # load config for database connection info

# spyglass.common has the most frequently used tables
import spyglass.common as sgc  # this import connects to the database

# spyglass.data_import has tools for inserting NWB files into the database
import spyglass.data_import as sgi
from spyglass.spikesorting.spikesorting_merge import (
    SpikeSortingOutput,
)  # This import is necessary for the spike sorting to be loaded properly
import spyglass.spikesorting.v1 as sgs
from spyglass.spikesorting.analysis.v1.group import SortedSpikesGroup
from spyglass.utils.nwb_helper_fn import get_nwb_copy_filename


def main():
    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/sub-SL18_ses-D19.nwb")
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)

    if sgc.Session & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Session & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}).delete()
    sgc.ProbeType.delete()
    if sgc.DataAcquisitionDevice & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.DataAcquisitionDevice & {"nwb_file_name": nwb_copy_file_name}).delete()

    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=True, raise_err=True)
    print("=== Session ===")
    print(sgc.Session & {"nwb_file_name": nwb_copy_file_name})
    print("=== NWB File ===")
    print(sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name})
    print("=== Electrode ===")
    print(sgc.Electrode & {"nwb_file_name": nwb_copy_file_name})
    print("=== Electrode Group ===")
    print(sgc.ElectrodeGroup & {"nwb_file_name": nwb_copy_file_name})
    print("=== Probe ===")
    print(sgc.Probe & {"probe_id": "my_probe_type"})
    print("=== Probe Shank ===")
    print(sgc.Probe.Shank & {"probe_id": "my_probe_type"})
    print("=== Probe Electrode ===")
    print(sgc.Probe.Electrode & {"probe_id": "my_probe_type"})
    print("=== Raw ===")
    print(sgc.Raw & {"nwb_file_name": nwb_copy_file_name})
    print("=== DataAcquisitionDevice ===")
    print(sgc.DataAcquisitionDevice & {"nwb_file_name": nwb_copy_file_name})
    electrical_series = (sgc.Raw & {"nwb_file_name": nwb_copy_file_name}).fetch_nwb()[0]["raw"]
    spyglass_raw_data = np.asarray(electrical_series.data)
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        nwb_raw_data = np.asarray(nwbfile.acquisition["ElectricalSeries_S01_F01_BOX_SLP"].data)
        np.testing.assert_array_equal(spyglass_raw_data, nwb_raw_data)


if __name__ == "__main__":
    main()
    print("Done!")
