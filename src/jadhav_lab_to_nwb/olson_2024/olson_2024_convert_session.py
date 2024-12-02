"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
import datetime
from zoneinfo import ZoneInfo
import shutil

from ndx_pose import (
    PoseEstimationSeries,
)  # TODO: remove after this issue gets fixed: https://github.com/catalystneuro/neuroconv/issues/1143
from neuroconv.utils import load_dict_from_file, dict_deep_update

from jadhav_lab_to_nwb.olson_2024 import Olson2024NWBConverter


def session_to_nwb(
    data_dir_path: str | Path, subject_id: str, session_id: str, output_dir_path: str | Path, stub_test: bool = False
):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)
    session_folder_path = data_dir_path / f"{subject_id}_{session_id}"
    nwbfile_path = nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Ephys
    file_path = (
        session_folder_path
        / "SL18_D19_S01_F01_BOX_SLP_20230503_112642"
        / "SL18_D19_S01_F01_BOX_SLP_20230503_112642.rec"
    )
    source_data.update(dict(Recording=dict(file_path=file_path)))
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
    file_paths = [
        session_folder_path
        / "SL18_D19_S01_F01_BOX_SLP_20230503_112642"
        / "SL18_D19_S01_F01_BOX_SLP_20230503_112642.1.h264"
    ]
    source_data.update(dict(Video=dict(file_paths=file_paths)))
    conversion_options.update(dict(Video=dict()))

    # Add DLC
    file_path = "/Volumes/T7/CatalystNeuro/Jadhav/SubLearnProject/SL18_D19/SL18_D19.DLC/SL18_D19_S01_F01_BOX_SLP_20230503_112642.1DLC_resnet50_SubLearnSleepBoxRedLightJun26shuffle1_100000.csv"
    source_data.update(dict(DeepLabCut=dict(file_path=file_path, subject_name=subject_id)))
    conversion_options.update(dict(DeepLabCut=dict()))

    # Add Behavior
    folder_path = session_folder_path / f"{session_folder_path.name}.DIO"
    source_data.update(dict(Behavior=dict(folder_path=folder_path)))
    conversion_options.update(dict(Behavior=dict()))

    converter = Olson2024NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    metadata["NWBFile"]["session_start_time"] = datetime.datetime(2023, 5, 3, 11, 26, 42, tzinfo=ZoneInfo("US/Eastern"))

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "olson_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Jadhav/SubLearnProject")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Jadhav/conversion_nwb")
    stub_test = True

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)

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
