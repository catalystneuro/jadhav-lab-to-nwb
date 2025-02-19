"""Ingest all data from a converted NWB file into a spyglass database."""

from pynwb import NWBHDF5IO
import numpy as np
import datajoint as dj
from pathlib import Path
import pandas as pd

dj_local_conf_path = "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_mock/dj_local_conf.json"
dj.config.load(dj_local_conf_path)  # load config for database connection info

# General Spyglass Imports
import spyglass.common as sgc  # this import connects to the database
import spyglass.data_import as sgi
from spyglass.utils.nwb_helper_fn import get_nwb_copy_filename

# Spike Sorting Imports
from spyglass.spikesorting.spikesorting_merge import SpikeSortingOutput
import spyglass.spikesorting.v1 as sgs
from spyglass.spikesorting.analysis.v1.group import SortedSpikesGroup
from spyglass.spikesorting.analysis.v1.group import UnitSelectionParams
from spyglass.spikesorting.analysis.v1.unit_annotation import UnitAnnotation

# Custom Table Imports
import sys

sys.path.append(
    "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/olson_2024/spyglass_extensions"
)
from epoch import TaskLEDs

# LFP Imports
import spyglass.lfp as sglfp
from spyglass.utils.nwb_helper_fn import estimate_sampling_rate
from pynwb.ecephys import ElectricalSeries, LFP


def insert_sorting(nwb_copy_file_name: str, units_table: pd.DataFrame):
    merge_id = str((SpikeSortingOutput.ImportedSpikeSorting & {"nwb_file_name": nwb_copy_file_name}).fetch1("merge_id"))

    UnitSelectionParams().insert_default()
    group_name = "all_units"
    SortedSpikesGroup().create_group(
        group_name=group_name,
        nwb_file_name=nwb_copy_file_name,
        keys=[{"spikesorting_merge_id": merge_id}],
    )
    annotation_to_type = {
        "nTrode": "label",
        "unitInd": "label",
        "globalID": "label",
        "nWaveforms": "quantification",
        "waveformFWHM": "quantification",
        "waveformPeakMinusTrough": "quantification",
    }
    group_key = {
        "nwb_file_name": nwb_copy_file_name,
        "sorted_spikes_group_name": group_name,
    }
    group_key = (SortedSpikesGroup & group_key).fetch1("KEY")
    _, unit_ids = SortedSpikesGroup().fetch_spike_data(group_key, return_unit_ids=True)

    for unit_key in unit_ids:
        unit_id = unit_key["unit_id"]
        for annotation, annotation_type in annotation_to_type.items():
            annotation_key = {
                **unit_key,
                "annotation": annotation,
                annotation_type: units_table.loc[unit_id][annotation],
            }
            UnitAnnotation().add_annotation(annotation_key, skip_duplicates=True)


def insert_lfp(nwb_copy_file_name: str, eseries_kwargs: dict):
    lfp_file_name = sgc.AnalysisNwbfile().create(nwb_copy_file_name)
    analysis_file_abspath = sgc.AnalysisNwbfile().get_abs_path(lfp_file_name)

    # Create dynamic table region and electrode series, write/close file
    with NWBHDF5IO(path=analysis_file_abspath, mode="a", load_namespaces=True) as io:
        nwbf = io.read()

        # get the indices of the electrodes in the electrode table
        electrodes_table = nwbf.electrodes.to_dataframe()
        lfp_electrode_indices = electrodes_table.index[electrodes_table.hasLFP].tolist()

        electrode_table_region = nwbf.create_electrode_table_region(lfp_electrode_indices, "filtered electrode table")
        eseries_kwargs["name"] = "filtered data"
        eseries_kwargs["electrodes"] = electrode_table_region
        es = ElectricalSeries(**eseries_kwargs)
        lfp_object_id = es.object_id
        ecephys_module = nwbf.create_processing_module(name="ecephys", description="ecephys module")
        ecephys_module.add(LFP(electrical_series=es))
        io.write(nwbf)

    sgc.AnalysisNwbfile().add(nwb_copy_file_name, lfp_file_name)

    lfp_electrode_group_name = "lfp_electrode_group"
    sglfp.lfp_electrode.LFPElectrodeGroup.create_lfp_electrode_group(
        nwb_file_name=nwb_copy_file_name,
        group_name=lfp_electrode_group_name,
        electrode_list=lfp_electrode_indices,
    )
    lfp_sampling_rate = estimate_sampling_rate(eseries_kwargs["timestamps"])
    key = {
        "nwb_file_name": nwb_copy_file_name,
        "lfp_electrode_group_name": lfp_electrode_group_name,
        "interval_list_name": "raw data valid times",
        "lfp_sampling_rate": lfp_sampling_rate,
        "lfp_object_id": lfp_object_id,
        "analysis_file_name": lfp_file_name,
    }
    sglfp.ImportedLFP.insert1(key, allow_direct_insert=True)
    sglfp.lfp_merge.LFPOutput.insert1(key, allow_direct_insert=True)


def insert_session(nwbfile_path: Path, rollback_on_fail: bool = True, raise_err: bool = False):
    """
    Insert all data from a converted NWB file into a spyglass database.

    Parameters
    ----------
    nwbfile_path : Path
        The path to the NWB file to insert.
    rollback_on_fail : bool
        Whether to rollback the transaction if an error occurs.
    raise_err : bool
        Whether to raise an error if an error occurs.
    """
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)
    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=rollback_on_fail, raise_err=raise_err)

    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        units_table = nwbfile.units.to_dataframe()
    insert_sorting(nwb_copy_file_name, units_table)
    TaskLEDs().make(key={"nwb_file_name": nwb_copy_file_name})
    with NWBHDF5IO(nwbfile_path, "r") as io:
        nwbfile = io.read()
        lfp_eseries = nwbfile.processing["ecephys"]["LFP"].electrical_series["ElectricalSeriesLFP"]
        timestamps = np.asarray(lfp_eseries.timestamps)
        data = np.asarray(lfp_eseries.data)
        eseries_kwargs = {
            "data": data,
            "timestamps": timestamps,
            "description": lfp_eseries.description,
        }
    insert_lfp(nwb_copy_file_name=nwb_copy_file_name, eseries_kwargs=eseries_kwargs)


def main():
    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/sub-SL18_ses-D19.nwb")
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)

    if sgc.Session & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Session & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}).delete()
    sgc.ProbeType.delete()
    if sgc.DataAcquisitionDevice & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.DataAcquisitionDevice & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.DIOEvents & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.DIOEvents & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.IntervalList & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.IntervalList & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.Task():
        sgc.Task.delete()
    if sgc.TaskEpoch():
        sgc.TaskEpoch.delete()
    if TaskLEDs():
        TaskLEDs().delete()
    if sgc.VideoFile & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.VideoFile & {"nwb_file_name": nwb_copy_file_name}).delete()

    insert_session(nwbfile_path, rollback_on_fail=True, raise_err=True)


if __name__ == "__main__":
    main()
    print("Done!")
