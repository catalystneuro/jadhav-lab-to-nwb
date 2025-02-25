"""Create a mock NWB file with spyglass-compatible epoch/task data for testing purposes."""

from pynwb.testing.mock.file import mock_NWBFile
from pynwb import NWBHDF5IO
from pynwb.core import DynamicTable
from pathlib import Path
from ndx_franklab_novela import CameraDevice


def main():
    nwbfile = mock_NWBFile(identifier="my_identifier", session_description="my_session_description")
    behavior_module = nwbfile.create_processing_module(name="behavior", description="behavior module")

    camera_device = CameraDevice(
        name="Camera 1",
        meters_per_pixel=1.0,
        model="my_model",
        lens="my_lens",
        camera_name="my_camera_name",
    )
    nwbfile.add_device(camera_device)

    tasks_module = nwbfile.create_processing_module(name="tasks", description="tasks module")
    num_tasks = 2
    for i in range(1, num_tasks + 1):
        task_table = DynamicTable(name=f"task_table_{i}", description="my task table")
        task_table.add_column(name="task_name", description="Name of the task.")
        task_table.add_column(name="task_description", description="Description of the task.")
        task_table.add_column(name="camera_id", description="Camera ID.")
        task_table.add_column(name="task_epochs", description="Task epochs.")
        task_table.add_row(
            task_name=f"task{i}", task_description=f"task{i} description", camera_id=[1], task_epochs=[i]
        )
        tasks_module.add(task_table)

    nwbfile.add_epoch_column(name="custom_data_string", description="Custom epoch column")
    nwbfile.add_epoch(start_time=0.0, stop_time=1.0, tags=["01"], custom_data_string="custom_value1")
    nwbfile.add_epoch(start_time=1.0, stop_time=2.0, tags=["02"], custom_data_string="custom_value2")

    nwbfile_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw/mock_epochs.nwb")
    if nwbfile_path.exists():
        nwbfile_path.unlink()
    with NWBHDF5IO(nwbfile_path, "w") as io:
        io.write(nwbfile)
    print(f"mock task NWB file successfully written at {nwbfile_path}")


if __name__ == "__main__":
    main()
