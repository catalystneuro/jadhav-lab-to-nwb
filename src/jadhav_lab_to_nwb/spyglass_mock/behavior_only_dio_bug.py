"See Issue: https://github.com/LorenFrankLab/spyglass/issues/1313"
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.ecephys import mock_ElectricalSeries
from pynwb.testing.mock.behavior import mock_TimeSeries
from pynwb.behavior import BehavioralEvents
from ndx_franklab_novela import DataAcqDevice, Probe, Shank, ShanksElectrode, NwbElectrodeGroup
from pynwb import NWBHDF5IO
import numpy as np
from pathlib import Path


def add_behavior(nwbfile):
    time_series = mock_TimeSeries(name="my_time_series", timestamps=np.arange(20), data=np.ones((20, 1)))
    behavioral_events = BehavioralEvents(name="behavioral_events", time_series=time_series)
    behavior_module = nwbfile.create_processing_module(name="behavior", description="behavior module")
    behavior_module.add(behavioral_events)


def write_nwbfile():
    nwbfile = mock_NWBFile(identifier="my_identifier", session_description="my_session_description")
    add_behavior(nwbfile)

    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/mock_behavior_only.nwb")
    if nwbfile_path.exists():
        nwbfile_path.unlink()
    with NWBHDF5IO(nwbfile_path, "w") as io:
        io.write(nwbfile)
    print(f"mock behavior NWB file successfully written at {nwbfile_path}")


def add_to_spyglass():
    import datajoint as dj

    dj_local_conf_path = "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_mock/dj_local_conf.json"
    dj.config.load(dj_local_conf_path)  # load config for database connection info

    # spyglass.common has the most frequently used tables
    import spyglass.common as sgc  # this import connects to the database

    # spyglass.data_import has tools for inserting NWB files into the database
    import spyglass.data_import as sgi
    from spyglass.utils.nwb_helper_fn import get_nwb_copy_filename

    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/mock_behavior_only.nwb")
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)

    if sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}).delete()
    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=True, raise_err=True)


if __name__ == "__main__":
    write_nwbfile()
    add_to_spyglass()
