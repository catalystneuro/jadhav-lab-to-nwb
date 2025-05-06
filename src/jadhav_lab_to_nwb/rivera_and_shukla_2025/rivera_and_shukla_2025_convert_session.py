"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import FilePath, DirectoryPath

from neuroconv.utils import load_dict_from_file, dict_deep_update

from jadhav_lab_to_nwb.rivera_and_shukla_2025 import RiveraAndShukla2025NWBConverter


def session_to_nwb(
    session_folder_path: DirectoryPath,
    subject_id: str,
    output_dir_path: DirectoryPath,
    stub_test: bool = False,
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
    file_paths = list(dio_folder_path.glob("*.h264"))
    video_timestamps_file_paths = list(dio_folder_path.glob("*.videoTimeStamps"))
    source_data.update(dict(Video=dict(file_paths=file_paths, video_timestamps_file_paths=video_timestamps_file_paths)))
    conversion_options.update(dict(Video=dict()))

    # # Add DLC
    file_paths = [
        file_path
        for file_path in dlc_folder_path.glob(r"*.h5")
        if not (file_path.name.startswith("._")) and "resnet50" in file_path.name
    ]
    subject_1, subject_2 = session_folder_path.parent.name.split("-")
    source_data.update(
        dict(
            DeepLabCut1=dict(
                file_paths=file_paths,
                video_timestamps_file_paths=video_timestamps_file_paths,
                subject_id=subject_1,
            ),
            DeepLabCut2=dict(
                file_paths=file_paths,
                video_timestamps_file_paths=video_timestamps_file_paths,
                subject_id=subject_2,
            ),
        )
    )
    conversion_options.update(dict(DeepLabCut1=dict()))
    conversion_options.update(dict(DeepLabCut2=dict()))

    # # Add Behavior
    # folder_path = session_folder_path / f"{session_folder_path.name}.DIO"
    # source_data.update(dict(Behavior=dict(folder_path=folder_path)))
    # conversion_options.update(dict(Behavior=dict()))

    # # Add Epoch
    # source_data.update(dict(Epoch=dict(epoch_folder_paths=epoch_folder_paths)))
    # conversion_options.update(dict(Epoch=dict()))

    converter = RiveraAndShukla2025NWBConverter(source_data=source_data)
    metadata = converter.get_metadata()

    # Add datetime to conversion
    session_start_time = datetime(2023, 7, 20, 0, 0, 0)  # TODO: Update this to the actual session start time
    est = ZoneInfo("US/Eastern")
    session_start_time = session_start_time.replace(tzinfo=est)
    metadata["NWBFile"]["session_start_time"] = session_start_time

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "rivera_and_shukla_2025_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)
    metadata["Subject"]["subject_id"] = subject_id

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Jadhav/CoopLearnProject")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw")
    stub_test = False

    # Example Session
    session_folder_path = data_dir_path / "CohortAS1" / "Social W" / "100%" / "XFN1-XFN3" / "07-20-2023"
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN1",
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
    session_to_nwb(
        session_folder_path=session_folder_path,
        subject_id="XFN3",
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
