from pynwb.testing.mock.file import mock_NWBFile
from ndx_franklab_novela import Probe, Shank, ShanksElectrode
from pynwb import NWBHDF5IO
from pathlib import Path


def create_nwbfile(nwbfile_path: Path):
    nwbfile = mock_NWBFile(identifier="my_identifier", session_description="my_session_description")
    electrode1 = ShanksElectrode(name="1", rel_x=1.0, rel_y=1.0, rel_z=1.0)
    shanks_electrodes1 = [electrode1]
    shank1 = Shank(name="1", shanks_electrodes=shanks_electrodes1)
    probe1 = Probe(
        name="my_probe1",
        id=1,
        probe_type="my_probe_type",
        units="my_units",
        probe_description="my_probe1_description",
        contact_side_numbering=False,
        contact_size=1.0,
        shanks=[shank1],
    )
    nwbfile.add_device(probe1)
    electrode2 = ShanksElectrode(name="2", rel_x=2.0, rel_y=2.0, rel_z=2.0)
    shanks_electrodes2 = [electrode2]
    shank2 = Shank(name="2", shanks_electrodes=shanks_electrodes2)
    probe2 = Probe(
        name="my_probe2",
        id=2,
        probe_type="my_probe_type",
        units="my_units",
        probe_description="my_probe2_description",
        contact_side_numbering=False,
        contact_size=2.0,
        shanks=[shank2],
    )
    nwbfile.add_device(probe2)

    # add processing module to make spyglass happy
    nwbfile.create_processing_module(name="behavior", description="dummy behavior module")

    if nwbfile_path.exists():
        nwbfile_path.unlink()
    with NWBHDF5IO(nwbfile_path, "w") as io:
        io.write(nwbfile)
    print(f"mock ephys NWB file successfully written at {nwbfile_path}")


def ingest_nwbfile(nwbfile_path: Path):
    # Import and connect to the database
    import datajoint as dj

    dj_local_conf_path = "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_mock/dj_local_conf.json"
    dj.config.load(dj_local_conf_path)  # load config for database connection info
    import spyglass.common as sgc  # this import connects to the database
    import spyglass.data_import as sgi
    from spyglass.utils.nwb_helper_fn import get_nwb_copy_filename

    # Insert the session
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    if sgc.Session & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Session & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.ProbeType & {"probe_type": "my_probe_type"}:
        (sgc.ProbeType & {"probe_type": "my_probe_type"}).delete()
    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=True, raise_err=True)

    # Check that the data was inserted correctly
    print("ProbeType")
    print(sgc.ProbeType())
    print("Probe")
    print(sgc.Probe())
    print("Probe.Shank")
    print(sgc.Probe.Shank())
    print("Probe.Shank.ShanksElectrode")
    print(sgc.Probe.Electrode())


def main():
    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/multi_probe_bug.nwb")
    create_nwbfile(nwbfile_path=nwbfile_path)
    ingest_nwbfile(nwbfile_path=nwbfile_path)


if __name__ == "__main__":
    main()
