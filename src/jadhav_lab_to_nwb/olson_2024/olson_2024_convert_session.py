"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
import datetime
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from jadhav_lab_to_nwb.olson_2024 import Olson2024NWBConverter


def session_to_nwb(data_dir_path: str | Path, output_dir_path: str | Path, stub_test: bool = False):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = "sample_session"
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()
    converter = Olson2024NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    datetime.datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern"))
    date = datetime.datetime.today()  # TODO: Get this from author
    metadata["NWBFile"]["session_start_time"] = date

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
    stub_test = False

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
