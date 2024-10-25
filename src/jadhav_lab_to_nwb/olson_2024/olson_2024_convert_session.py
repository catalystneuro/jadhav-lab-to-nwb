"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
import datetime
from zoneinfo import ZoneInfo
import shutil

from neuroconv.utils import load_dict_from_file, dict_deep_update
from neuroconv.datainterfaces import SpikeGadgetsRecordingInterface
from neuroconv import ConverterPipe

from jadhav_lab_to_nwb.olson_2024 import Olson2024NWBConverter


def session_to_nwb(data_dir_path: str | Path, output_dir_path: str | Path, stub_test: bool = False):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = "sample_session"
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    data_interfaces = dict()
    conversion_options = dict()

    # Add Ephys Recording Interface
    file_path = data_dir_path / f"{data_dir_path.name}.rec"
    RecordingInterface = SpikeGadgetsRecordingInterface(file_path=file_path)
    # channel_ids = converter.data_interface_objects["Recording"].recording_extractor.get_channel_ids()
    # converter.data_interface_objects["Recording"].recording_extractor.set_property(
    #     key="group_name",
    #     ids=channel_ids,
    #     values=["CA1_R"]*len(channel_ids),
    # )
    data_interfaces.update(dict(Recording=RecordingInterface))
    conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

    converter = ConverterPipe(data_interfaces=data_interfaces)

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
    data_dir_path = Path(
        "/Volumes/T7/CatalystNeuro/Jadhav/SubLearnProject/SL18_D19/SL18_D19_S01_F01_BOX_SLP_20230503_112642"
    )
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Jadhav/conversion_nwb")
    stub_test = True

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
