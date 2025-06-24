"""Session conversion script for Olson 2024 dataset.

This module provides the main conversion script for converting individual sessions
from the Olson 2024 electrophysiology dataset to NWB format. It orchestrates the
conversion of all data modalities (ephys, behavior, video, pose estimation) for
a complete experimental session.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from natsort import natsorted

from neuroconv.utils import load_dict_from_file, dict_deep_update

from jadhav_lab_to_nwb.olson_2024 import Olson2024NWBConverter


def get_start_datetime(epoch_folder_name: str) -> datetime:
    """Extract session start datetime from epoch folder name.

    Parses the timestamp from epoch folder names with format:
    {subject}_{session}_S{epoch}_F{file}_{YYYYMMDD}_{HHMMSS}

    Parameters
    ----------
    epoch_folder_name : str
        Name of the epoch folder containing timestamp information.

    Returns
    -------
    datetime
        The start datetime of the epoch extracted from the folder name.
    """
    split_name = epoch_folder_name.split("_")
    start_datetime = datetime.strptime(split_name[-2] + "_" + split_name[-1], "%Y%m%d_%H%M%S")
    return start_datetime


def session_to_nwb(
    data_dir_path: str | Path, subject_id: str, session_id: str, output_dir_path: str | Path, stub_test: bool = False
):
    """Convert a complete experimental session to NWB format.

    This function orchestrates the conversion of all data modalities from a single
    experimental session including electrophysiology, spike sorting, LFP, behavioral
    video, pose estimation, and digital I/O data. It automatically discovers epoch
    folders and configures all data interfaces for the NWB converter.

    Parameters
    ----------
    data_dir_path : str or Path
        Path to the root data directory containing session folders.
    subject_id : str
        Subject identifier (e.g., 'SL18').
    session_id : str
        Session identifier (e.g., 'D19').
    output_dir_path : str or Path
        Path to directory where NWB files will be saved.
    stub_test : bool, optional
        If True, creates a minimal NWB file for testing purposes with reduced
        data size and only the first epoch. Default is False.

    Notes
    -----
    Expected directory structure:
    data_dir_path/
    └── {subject_id}_{session_id}/
        ├── {subject_id}_{session_id}_S{epoch}_F{file}_{timestamp}/
        │   ├── {epoch_name}.rec
        │   ├── {epoch_name}.trodesComments
        │   ├── {epoch_name}.1.mp4
        │   └── {epoch_name}.1.videoTimeStamps
        ├── {session_name}.SpikesFinal/
        ├── {session_name}.ExportedUnitStats/
        ├── {session_name}.LFP/
        ├── {session_name}.DLC/
        └── {session_name}.DIO/
    """

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    session_folder_path = data_dir_path / f"{subject_id}_{session_id}"
    if stub_test:
        nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-{session_id}_stub.nwb"
    else:
        nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-{session_id}.nwb"
    if nwbfile_path.exists():
        nwbfile_path.unlink()

    # Get epoch info
    epoch_folder_paths = list(session_folder_path.glob(rf"{session_folder_path.name}_S[0-9][0-9]_F[0-9][0-9]_*"))
    epoch_folder_paths = natsorted(epoch_folder_paths)

    source_data = dict()
    conversion_options = dict()

    # Add Ephys
    file_paths = [epoch_folder_path / f"{epoch_folder_path.name}.rec" for epoch_folder_path in epoch_folder_paths]
    comments_file_paths = [
        epoch_folder_path / f"{epoch_folder_path.name}.trodesComments" for epoch_folder_path in epoch_folder_paths
    ]
    if stub_test:  # TODO: Remove after this issue gets fixed: https://github.com/LorenFrankLab/spyglass/issues/1240
        file_paths = file_paths[:1]
        comments_file_paths = comments_file_paths[:1]
    source_data.update(dict(Recording=dict(file_paths=file_paths, comments_file_paths=comments_file_paths)))
    conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

    # Add Sorting
    spike_times_folder_path = session_folder_path / f"{session_folder_path.name}.SpikesFinal"
    unit_stats_folder_path = session_folder_path / f"{session_folder_path.name}.ExportedUnitStats"
    source_data.update(
        dict(
            Sorting=dict(spike_times_folder_path=spike_times_folder_path, unit_stats_folder_path=unit_stats_folder_path)
        )
    )
    conversion_options.update(dict(Sorting=dict()))

    # Add LFP
    folder_path = session_folder_path / f"{session_folder_path.name}.LFP"
    source_data.update(dict(LFP=dict(folder_path=folder_path)))
    conversion_options.update(dict(LFP=dict(stub_test=stub_test)))

    # Add Video
    file_paths, video_timestamps_file_paths = [], []
    for epoch_folder_path in epoch_folder_paths:
        file_path = epoch_folder_path / f"{epoch_folder_path.name}.1.mp4"
        video_timestamps_file_path = epoch_folder_path / f"{epoch_folder_path.name}.1.videoTimeStamps"
        file_paths.append(file_path)
        video_timestamps_file_paths.append(video_timestamps_file_path)
    source_data.update(dict(Video=dict(file_paths=file_paths, video_timestamps_file_paths=video_timestamps_file_paths)))
    conversion_options.update(dict(Video=dict()))

    # Add DLC
    dlc_folder_path = session_folder_path / f"{session_folder_path.name}.DLC"
    file_paths = [file_path for file_path in dlc_folder_path.glob(r"*.csv") if not (file_path.name.startswith("._"))]
    source_data.update(dict(DeepLabCut=dict(file_paths=file_paths)))
    conversion_options.update(dict(DeepLabCut=dict()))

    # Add Behavior
    folder_path = session_folder_path / f"{session_folder_path.name}.DIO"
    source_data.update(dict(Behavior=dict(folder_path=folder_path)))
    conversion_options.update(dict(Behavior=dict()))

    # Add Epoch
    source_data.update(dict(Epoch=dict(video_timestamps_file_paths=video_timestamps_file_paths)))
    conversion_options.update(dict(Epoch=dict()))

    converter = Olson2024NWBConverter(source_data=source_data)
    metadata = converter.get_metadata()

    # Add datetime to conversion
    session_start_time = get_start_datetime(epoch_folder_paths[0].name)
    est = ZoneInfo("US/Eastern")
    session_start_time = session_start_time.replace(tzinfo=est)
    metadata["NWBFile"]["session_start_time"] = session_start_time

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "olson_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Jadhav/SubLearnProject")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw")
    stub_test = False

    # Example Session
    subject_id = "SL18"
    session_id = "D19"
    session_to_nwb(
        data_dir_path=data_dir_path,
        subject_id=subject_id,
        session_id=session_id,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
