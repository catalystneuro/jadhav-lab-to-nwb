"See Issue: https://github.com/LorenFrankLab/spyglass/issues/1321"
from pynwb.testing.mock.file import mock_NWBFile, mock_Subject
from pynwb import NWBHDF5IO
import numpy as np
from pathlib import Path

from ndx_pose import (
    PoseEstimationSeries,
    PoseEstimation,
    Skeleton,
    Skeletons,
)


def add_pose_estimation(nwbfile):
    subject = mock_Subject(nwbfile=nwbfile)
    skeleton = Skeleton(
        name="subject1_skeleton",
        nodes=["front_left_paw", "body", "front_right_paw"],
        edges=np.array([[0, 1], [1, 2]], dtype="uint8"),
        subject=subject,
    )
    skeletons = Skeletons(skeletons=[skeleton])

    data = np.random.rand(100, 2)  # num_frames x (x, y) but can be (x, y, z)
    confidence = np.random.rand(100)  # a confidence value for every frame
    reference_frame = "(0,0) corresponds to top left corner"
    confidence_definition = "Softmax output of the deep neural network."

    pose_estimation_series = [
        PoseEstimationSeries(
            name="PoseEstimationSeries",
            description="Test data with starting time and rate instead of timestamps.",
            data=data,
            reference_frame=reference_frame,
            starting_time=0.0,
            rate=30.0,
            confidence=confidence,
            confidence_definition=confidence_definition,
        ),
    ]
    pose_estimation = PoseEstimation(
        name="PoseEstimation",
        pose_estimation_series=pose_estimation_series,
        description="Estimated positions of front paws of subject1 using DeepLabCut.",
        skeleton=skeleton,
    )

    behavior_module = nwbfile.create_processing_module(name="behavior", description="behavior module")
    behavior_module.add(pose_estimation)
    behavior_module.add(skeletons)


def write_nwbfile():
    nwbfile = mock_NWBFile(identifier="my_identifier", session_description="my_session_description")
    add_pose_estimation(nwbfile)

    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/rate_based_pose_estimation_bug.nwb")
    if nwbfile_path.exists():
        nwbfile_path.unlink()
    with NWBHDF5IO(nwbfile_path, "w") as io:
        io.write(nwbfile)
    print(f"NWB file successfully written at {nwbfile_path}")


def add_to_spyglass():
    import datajoint as dj

    dj_local_conf_path = "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_mock/dj_local_conf.json"
    dj.config.load(dj_local_conf_path)  # load config for database connection info

    # spyglass.common has the most frequently used tables
    import spyglass.common as sgc  # this import connects to the database

    # spyglass.data_import has tools for inserting NWB files into the database
    import spyglass.data_import as sgi
    from spyglass.utils.nwb_helper_fn import get_nwb_copy_filename

    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/rate_based_pose_estimation_bug.nwb")
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)

    if sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}).delete()
    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=True, raise_err=True)


if __name__ == "__main__":
    write_nwbfile()
    add_to_spyglass()
