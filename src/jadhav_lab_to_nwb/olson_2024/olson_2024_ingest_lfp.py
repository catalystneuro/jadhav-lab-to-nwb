"""Ingest spike sorting data from a converted NWB file into a spyglass database."""

import datajoint as dj
from pathlib import Path
import pandas as pd
from pynwb import NWBHDF5IO
import numpy as np

dj_local_conf_path = "/Users/pauladkisson/Documents/CatalystNeuro/JadhavConv/jadhav-lab-to-nwb/src/jadhav_lab_to_nwb/spyglass_mock/dj_local_conf.json"
dj.config.load(dj_local_conf_path)  # load config for database connection info

# spyglass.common has the most frequently used tables
import spyglass.common as sgc  # this import connects to the database

# spyglass.data_import has tools for inserting NWB files into the database
import spyglass.data_import as sgi
from spyglass.utils.nwb_helper_fn import get_nwb_copy_filename

# Spike sorting specific imports
from spyglass.spikesorting.spikesorting_merge import (
    SpikeSortingOutput,
)
import spyglass.lfp as sglfp
from spyglass.utils.nwb_helper_fn import estimate_sampling_rate
from pynwb.ecephys import ElectricalSeries, LFP
from pynwb import NWBHDF5IO


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

    lfp_electrode_group_name = "my_lfp_electrode_group"
    sglfp.lfp_electrode.LFPElectrodeGroup.create_lfp_electrode_group(
        nwb_file_name=nwb_copy_file_name,
        group_name=lfp_electrode_group_name,
        electrode_list=lfp_electrode_indices,
    )
    print(f"{eseries_kwargs['timestamps'] = }")
    lfp_sampling_rate = estimate_sampling_rate(eseries_kwargs["timestamps"])
    print(f"{lfp_sampling_rate = }")
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


def main():
    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/sub-SL18_ses-D19.nwb")
    nwb_copy_file_name = get_nwb_copy_filename(nwbfile_path.name)

    if sgc.Session & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Session & {"nwb_file_name": nwb_copy_file_name}).delete()
    if sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}:
        (sgc.Nwbfile & {"nwb_file_name": nwb_copy_file_name}).delete()
    sgc.ProbeType.delete()

    sgi.insert_sessions(str(nwbfile_path), rollback_on_fail=True, raise_err=True)
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

    print("=== AnalysisNwbfile ===")
    print(sgc.AnalysisNwbfile & {"nwb_file_name": nwb_copy_file_name})
    print("=== LFPElectrodeGroup ===")
    print(sglfp.lfp_electrode.LFPElectrodeGroup & {"nwb_file_name": nwb_copy_file_name})
    print("=== ImportedLFP ===")
    print(sglfp.ImportedLFP & {"nwb_file_name": nwb_copy_file_name})
    print("=== LFPOutput ===")
    print(sglfp.lfp_merge.LFPOutput & {"nwb_file_name": nwb_copy_file_name})


if __name__ == "__main__":
    main()
    print("Done!")
