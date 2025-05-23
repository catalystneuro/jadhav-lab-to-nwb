import datajoint as dj
from spyglass.utils import SpyglassMixin
from spyglass.common.common_task import Task
from spyglass.common.common_nwbfile import Nwbfile
from spyglass.utils.nwb_helper_fn import get_nwb_file

schema = dj.schema("task_leds")


@schema
class TaskLEDs(SpyglassMixin, dj.Imported):
    """Table to accompany spyglass.common.Task with extra information about LEDs used in tasks."""

    definition = """
    -> Task # Inherit primary key from Task
    led_name : varchar(32) # string of max length 32
    ---
    led_configuration : varchar(32) # string of max length 32
    led_position : varchar(32) # string of max length 32
    """

    def make(self, key):
        """Populate TaskLEDs from the epoch table in the NWB file."""

        nwb_file_name = key["nwb_file_name"]
        nwb_file_abspath = Nwbfile().get_abs_path(nwb_file_name)
        nwbf = get_nwb_file(nwb_file_abspath)

        # Create a list of dictionaries to insert
        inserts = []
        for name, task_table in nwbf.processing["tasks"].data_interfaces.items():
            task_table = task_table.to_dataframe()
            for _, row in task_table.iterrows():
                task_name = row["task_name"]
                led_configuration = row["led_configuration"]
                led_names = row["led_list"].split(",")
                led_positions = row["led_positions"].split(",")

                for led_name, led_position in zip(led_names, led_positions):
                    inserts.append(
                        {
                            "task_name": task_name,
                            "led_name": led_name,
                            "led_configuration": led_configuration,
                            "led_position": led_position,
                        }
                    )
        self.insert(inserts, allow_direct_insert=True, skip_duplicates=True)
