"""Session conversion script for Rivera and Shukla 2025 dataset.

This module provides the primary conversion function for converting individual
sessions from the Rivera and Shukla 2025 social behavior dataset to NWB format.
It handles file discovery, data organization, metadata configuration, and
conversion orchestration for multi-subject social behavior experiments.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import FilePath, DirectoryPath
from natsort import natsorted
from typing import Literal
from h5py import is_hdf5

from neuroconv.utils import load_dict_from_file, dict_deep_update

from jadhav_lab_to_nwb.rivera_and_shukla_2025 import RiveraAndShukla2025NWBConverter
from jadhav_lab_to_nwb.utils.utils import rivera_and_shukla_2025_get_epoch_name


def session_to_nwb(
    session_folder_path: DirectoryPath,
    subject_id: str,
    output_dir_path: DirectoryPath,
    experimental_condition: Literal["100%", "50%", "Opaque"],
    stub_test: bool = False,
    verbose: bool = False,
):
    """Convert a single session from Rivera and Shukla 2025 dataset to NWB format.

    Performs complete conversion of a social behavior session including video,
    behavioral events, pose estimation, and epoch data. Handles file discovery,
    data organization, temporal alignment, and metadata configuration for
    multi-subject experiments.

    The function automatically discovers and organizes data files by epoch,
    configures subject-specific metadata, applies experimental condition
    information, and runs the full conversion pipeline.

    Parameters
    ----------
    session_folder_path : DirectoryPath
        Path to the session folder containing 'DIO data' and 'DLC data' subfolders.
        Session folder name should be in MM-DD-YYYY format.
    subject_id : str
        Identifier for the subject being converted (e.g., 'XFN1', 'XFN3').
        Must match one of the subjects in the session folder parent name.
    output_dir_path : DirectoryPath
        Directory path where the converted NWB file will be saved.
        File will be named 'sub-{subject_id}_ses-{session_id}.nwb'.
    experimental_condition : Literal["100%", "50%", "Opaque"]
        Experimental condition for the session, used to set session description.
        - "100%": 100% reward probability condition
        - "50%": 50% reward probability condition
        - "Opaque": Opaque barrier condition
    stub_test : bool, optional
        Whether to run conversion in stub test mode (not implemented), by default False.
    verbose : bool, optional
        Whether to print progress messages during conversion, by default False.

    Notes
    -----
    The function expects a specific directory structure:
    - session_folder_path/DIO data/Raw/ (contains .h264, .videoTimeStamps, .stateScriptLog)
    - session_folder_path/DLC data/Raw/ (contains .h5 pose estimation files)

    Files are automatically organized by epoch using the naming convention parser.
    Missing DLC data is handled gracefully with optional conversion.
    """
    session_folder_path = Path(session_folder_path)
    session_date = session_folder_path.name
    session_id = f"{session_date}-{experimental_condition}".strip("%")  # Spyglass doesn't allow % in the file name
    dio_folder_path = session_folder_path / "DIO data" / "Raw"
    dlc_folder_path = session_folder_path / "DLC data" / "Raw"
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-{session_id}.nwb"
    if nwbfile_path.exists():
        nwbfile_path.unlink()

    source_data = dict()
    conversion_options = dict()

    # Add Video
    file_paths = [file_path for file_path in dio_folder_path.glob("*.mp4") if not file_path.name.startswith("._")]
    file_paths = natsorted(file_paths)
    # log07-15-2023(3-XFN3-XFN1).1.mp4 is just a video of the mazes without behavior --> skipping
    file_paths = [file_path for file_path in file_paths if file_path.name != "log07-15-2023(3-XFN3-XFN1).1.mp4"]
    video_timestamps_file_paths = natsorted(
        [file_path for file_path in dio_folder_path.glob("*.videoTimeStamps") if not file_path.name.startswith("._")]
    )
    epoch_name_to_file_paths, epoch_name_to_timestamps_file_paths = {}, {}
    for file_path, video_timestamps_file_path in zip(file_paths, video_timestamps_file_paths, strict=True):
        file_epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_path.name)
        timestamps_epoch_name = rivera_and_shukla_2025_get_epoch_name(name=video_timestamps_file_path.name)
        assert file_epoch_name == timestamps_epoch_name, "Video files were not sorted correctly."
        if file_epoch_name not in epoch_name_to_file_paths:
            epoch_name_to_file_paths[file_epoch_name] = []
        epoch_name_to_file_paths[file_epoch_name].append(file_path)
        if timestamps_epoch_name not in epoch_name_to_timestamps_file_paths:
            epoch_name_to_timestamps_file_paths[timestamps_epoch_name] = []
        epoch_name_to_timestamps_file_paths[timestamps_epoch_name].append(video_timestamps_file_path)
    file_paths = []
    video_timestamps_file_paths = []
    for epoch_name in natsorted(epoch_name_to_file_paths.keys()):
        file_paths.append(natsorted(epoch_name_to_file_paths[epoch_name]))
        video_timestamps_file_paths.append(natsorted(epoch_name_to_timestamps_file_paths[epoch_name]))
    source_data.update(dict(Video=dict(file_paths=file_paths, video_timestamps_file_paths=video_timestamps_file_paths)))
    conversion_options.update(dict(Video=dict()))

    # Add DLC
    file_paths = [
        file_path
        for file_path in dlc_folder_path.glob(r"*.h5")
        if not (file_path.name.startswith("._")) and "resnet50" in file_path.name and is_hdf5(file_path)
    ]
    if len(file_paths) > 0:
        file_paths = natsorted(file_paths)
        epoch_name_to_file_paths = {}
        for file_path in file_paths:
            file_epoch_name = rivera_and_shukla_2025_get_epoch_name(name=file_path.name)
            if file_epoch_name not in epoch_name_to_file_paths:
                epoch_name_to_file_paths[file_epoch_name] = []
            epoch_name_to_file_paths[file_epoch_name].append(file_path)
        file_paths = []
        for epoch_name in natsorted(epoch_name_to_file_paths.keys()):
            file_paths.append(natsorted(epoch_name_to_file_paths[epoch_name]))
        subject_1, subject_2 = session_folder_path.parent.name.split("-")
        source_data.update(
            dict(
                DeepLabCut1=dict(
                    file_paths=file_paths,
                    subject_id=subject_1,
                ),
                DeepLabCut2=dict(
                    file_paths=file_paths,
                    subject_id=subject_2,
                ),
            )
        )
        conversion_options.update(dict(DeepLabCut1=dict()))
        conversion_options.update(dict(DeepLabCut2=dict()))
    else:
        if verbose:
            print(f"No DLC data found for session {session_id} and subject {subject_id}. Skipping DLC conversion.")

    # Add Behavior
    file_paths = natsorted(list(dio_folder_path.glob("*.stateScriptLog")))
    source_data.update(dict(Behavior=dict(file_paths=file_paths)))
    conversion_options.update(dict(Behavior=dict()))

    # Add Epoch
    source_data.update(dict(Epoch=dict(video_timestamps_file_paths=video_timestamps_file_paths)))
    conversion_options.update(dict(Epoch=dict()))

    converter = RiveraAndShukla2025NWBConverter(source_data=source_data, verbose=verbose)
    metadata = converter.get_metadata()

    # Add datetime to conversion
    session_start_time = datetime.strptime(session_date, "%m-%d-%Y")
    est = ZoneInfo("US/Eastern")
    session_start_time = session_start_time.replace(tzinfo=est)
    metadata["NWBFile"]["session_start_time"] = session_start_time

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "rivera_and_shukla_2025_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)
    metadata["Subject"]["subject_id"] = subject_id

    # Add genotype
    metadata["Subject"]["genotype"] = metadata["SubjectMaps"]["subject_id_to_genotype"][subject_id]

    # Add session_id and description
    metadata["NWBFile"]["session_id"] = session_id
    session_description = metadata["SessionMaps"]["condition_to_session_description"][experimental_condition]
    metadata["NWBFile"]["session_description"] = session_description

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)

    if verbose:
        print(f"Successfully converted session {session_id} for subject {subject_id} to NWB format.")


def main():
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Jadhav/CoopLearnProject")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Jadhav/conversion_nwb/rivera_and_shukla_2025")
    output_dir_path.mkdir(parents=True, exist_ok=True)
    stub_test = False
    verbose = True

    # Example Session 100% reward
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN1-XFN3" / "07-20-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN1",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )

    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN3",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session 50% reward
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "50%" / "XFN1-XFN3" / "08-08-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN1",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN3",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session Opaque
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "Opaque" / "XFN1-XFN3" / "08-16-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN1",
        output_dir_path=output_dir_path,
        experimental_condition="Opaque",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN3",
        output_dir_path=output_dir_path,
        experimental_condition="Opaque",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session WT
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN2-XFN4" / "07-19-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN2",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN4",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session Single Epoch
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN2-XFN4" / "07-15-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN2",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN4",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session DIO-only
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "50%" / "XFN1-XFN3" / "08-03-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN1",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN3",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session Multiple Videos (segments) for a single epoch
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "50%" / "XFN1-XFN3" / "08-07-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN1",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN3",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session with corrupted hdf5 files
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN1-XFN3" / "07-27-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN1",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN3",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session with incomplete epochs and mismatched timestamps
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN1-XFN3" / "07-15-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN1",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN3",
        output_dir_path=output_dir_path,
        experimental_condition="100%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session with missing DLC epochs
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "50%" / "XFN1-XFN3" / "08-16-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN1",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN3",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session with missing DLC segment
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "50%" / "XFN2-XFN4" / "08-03-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN2",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN4",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )

    # Example Session with ~~~ in the stateScriptLog
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "50%" / "XFN2-XFN4" / "09-21-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN2",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN4",
        output_dir_path=output_dir_path,
        experimental_condition="50%",
        stub_test=stub_test,
        verbose=verbose,
    )


if __name__ == "__main__":
    main()
