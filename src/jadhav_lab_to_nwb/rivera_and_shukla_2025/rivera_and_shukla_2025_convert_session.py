"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import shutil

from ndx_pose import (
    PoseEstimationSeries,
)  # TODO: remove after this issue gets fixed: https://github.com/catalystneuro/neuroconv/issues/1143
from neuroconv.utils import load_dict_from_file, dict_deep_update

from jadhav_lab_to_nwb.rivera_and_shukla_2025 import RiveraAndShukla2025NWBConverter


def session_to_nwb(
    data_dir_path: str | Path, subject_id: str, session_id: str, output_dir_path: str | Path, stub_test: bool = False
):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    session_folder_path = data_dir_path / f"{subject_id}_{session_id}"
    nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-{session_id}.nwb"
    if nwbfile_path.exists():
        nwbfile_path.unlink()

    # Get epoch info
    epoch_folder_paths = list(session_folder_path.glob(rf"{session_folder_path.name}_S[0-9][0-9]_F[0-9][0-9]_*"))
    epoch_folder_paths = sorted(epoch_folder_paths)
    if stub_test:  # TODO: Remove after this issue gets fixed: https://github.com/LorenFrankLab/spyglass/issues/1240
        epoch_folder_paths = epoch_folder_paths[:1]

    source_data = dict()
    conversion_options = dict()

    # Add Ephys
    file_paths = [epoch_folder_path / f"{epoch_folder_path.name}.rec" for epoch_folder_path in epoch_folder_paths]
    comments_file_paths = [
        epoch_folder_path / f"{epoch_folder_path.name}.trodesComments" for epoch_folder_path in epoch_folder_paths
    ]
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
        file_path = epoch_folder_path / f"{epoch_folder_path.name}.1.h264"
        video_timestamps_file_path = epoch_folder_path / f"{epoch_folder_path.name}.1.videoTimeStamps"
        file_paths.append(file_path)
        video_timestamps_file_paths.append(video_timestamps_file_path)
    source_data.update(dict(Video=dict(file_paths=file_paths, video_timestamps_file_paths=video_timestamps_file_paths)))
    conversion_options.update(dict(Video=dict()))

    # Add DLC
    dlc_folder_path = session_folder_path / f"{session_folder_path.name}.DLC"
    file_paths = [file_path for file_path in dlc_folder_path.glob(r"*.csv") if not (file_path.name.startswith("._"))]
    if stub_test:  # TODO: Remove after this issue gets fixed: https://github.com/LorenFrankLab/spyglass/issues/1240
        file_paths = file_paths[:1]
    source_data.update(
        dict(
            DeepLabCut=dict(
                file_paths=file_paths, video_timestamps_file_paths=video_timestamps_file_paths, subject_name=subject_id
            )
        )
    )
    conversion_options.update(dict(DeepLabCut=dict()))

    # Add Behavior
    folder_path = session_folder_path / f"{session_folder_path.name}.DIO"
    source_data.update(dict(Behavior=dict(folder_path=folder_path)))
    conversion_options.update(dict(Behavior=dict()))

    # Add Epoch
    source_data.update(dict(Epoch=dict(epoch_folder_paths=epoch_folder_paths)))
    conversion_options.update(dict(Epoch=dict()))

    converter = Olson2024NWBConverter(source_data=source_data)
    metadata = converter.get_metadata()

    # Add datetime to conversion
    session_start_time = get_start_datetime(epoch_folder_paths[0].name)
    est = ZoneInfo("US/Eastern")
    session_start_time = session_start_time.replace(tzinfo=est)
    metadata["NWBFile"]["session_start_time"] = session_start_time

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "rivera_and_shukla_2025_metadata.yaml"
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
