"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import FilePath, DirectoryPath
from natsort import natsorted
from typing import Literal

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
    session_folder_path = Path(session_folder_path)
    session_id = session_folder_path.name
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
    file_paths = natsorted(list(dio_folder_path.glob("*.h264")))
    video_timestamps_file_paths = natsorted(list(dio_folder_path.glob("*.videoTimeStamps")))
    epoch_name_to_file_paths, epoch_name_to_timestamps_file_paths = {}, {}
    for file_path, video_timestamps_file_path in zip(file_paths, video_timestamps_file_paths):
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
        if not (file_path.name.startswith("._")) and "resnet50" in file_path.name
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
    session_start_time = datetime.strptime(session_id, "%m-%d-%Y")
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

    # Add session description
    session_description = metadata["SessionMaps"]["condition_to_session_description"][experimental_condition]
    metadata["NWBFile"]["session_description"] = session_description

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)

    if verbose:
        print(f"Successfully converted session {session_id} for subject {subject_id} to NWB format.")


def main():
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Jadhav/CoopLearnProject")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw")
    stub_test = False
    verbose = True

    # # Example Session 100% reward
    # session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN1-XFN3" / "07-20-2023"
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN1",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="100%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )

    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN3",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="100%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )

    # # Example Session 50% reward
    # session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "50%" / "XFN1-XFN3" / "08-08-2023"
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN1",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="50%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN3",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="50%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )

    # # Example Session Opaque
    # session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "Opaque" / "XFN1-XFN3" / "08-16-2023"
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN1",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="Opaque",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN3",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="Opaque",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )

    # # Example Session WT
    # session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN2-XFN4" / "07-19-2023"
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN2",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="100%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN4",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="100%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )

    # # Example Session Single Epoch
    # session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN2-XFN4" / "07-15-2023"
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN2",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="100%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN4",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="100%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )

    # # Example Session DIO-only
    # session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN1-XFN3" / "07-17-2023"
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN1",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="100%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )
    # session_to_nwb(
    #     session_folder_path=session_folder_path,
    #     subject_id="XFN3",
    #     output_dir_path=output_dir_path,
    #     experimental_condition="100%",
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )

    #     - Some of the sessions (ex. CoopLearnProject/CohortAS1/Social W/100%/XFN2-XFN4/07-14-2023) has a different number of timestamps for video and DLC
    # - Some of the sessions (ex. CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/08-16-2023) are missing DLC epochs
    # - Some of the sessions (ex. CoopLearnProject/CohortAS1/Social W/100%/XFN1-XFN3/07-15-2023) have incomplete epochs
    # - Some of the sessions (ex. CoopLearnProject/CohortAS1/Social W/100%/XFN1-XFN3/07-27-2023) have corrupted hdf5 files --> investigate
    # - Some of the sessions (ex. CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/08-07-2023) have multiple videos/epoch --> need to investigate

    # Example Session Multiple Videos for a single epoch
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN2-XFN4" / "07-24-2023"
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


if __name__ == "__main__":
    main()
