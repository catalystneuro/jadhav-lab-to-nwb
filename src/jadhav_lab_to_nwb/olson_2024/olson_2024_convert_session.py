"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
import datetime
from zoneinfo import ZoneInfo
import shutil
from xml.etree import ElementTree

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
    recording_extractor = RecordingInterface.recording_extractor
    channel_ids = recording_extractor.get_channel_ids()
    channel_names = recording_extractor.get_property(key="channel_name", ids=channel_ids)
    header = get_spikegadgets_header(file_path)
    hwChan_to_nTrode = extract_hwChan_to_nTrode(header)
    group_names = []
    for channel_name in channel_names:
        hwChan = channel_name.split("hwChan")[-1]
        nTrode = hwChan_to_nTrode[hwChan]
        group_names.append(f"nTrode{nTrode}")
    recording_extractor.set_property(key="group_name", ids=channel_ids, values=group_names)

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


def get_spikegadgets_header(file_path: str | Path):
    """Get the header information from a SpikeGadgets .rec file.

    This function reads the .rec file until the "</Configuration>" tag to extract the header information.

    Parameters
    ----------
    file_path : str | Path
        Path to the .rec file.

    Returns
    -------
    str
        The header information from the .rec file.

    Raises
    ------
    ValueError
        If the header does not contain "</Configuration>".
    """
    header_size = None
    with open(file_path, mode="rb") as f:
        while True:
            line = f.readline()
            if b"</Configuration>" in line:
                header_size = f.tell()
                break

        if header_size is None:
            ValueError("SpikeGadgets: the xml header does not contain '</Configuration>'")

        f.seek(0)
        return f.read(header_size).decode("utf8")


def extract_hwChan_to_nTrode(header_txt):
    """Extract the hardware channel to tetrode mapping from the header text.

    Parameters
    ----------
    header_txt : str
        The header text.

    Returns
    -------
    dict
        A dictionary mapping hardware channel IDs to tetrode IDs.
    """
    root = ElementTree.fromstring(header_txt)
    sconf = root.find("SpikeConfiguration")
    hwChan_to_nTrode = dict()
    for tetrode in sconf.findall("SpikeNTrode"):
        nTrode = tetrode.attrib["id"]
        for electrode in tetrode.findall("SpikeChannel"):
            hwChan = electrode.attrib["hwChan"]
            hwChan_to_nTrode[hwChan] = nTrode
    return hwChan_to_nTrode


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
