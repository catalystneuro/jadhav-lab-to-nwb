"""SpyGlass extension for task LED configuration data.

This module provides a custom DataJoint table that extends SpyGlass functionality
to store LED configuration information for behavioral tasks. It extracts LED
setup details from NWB files and stores them in a structured database format
for analysis and querying.
"""
import datajoint as dj
from spyglass.utils import SpyglassMixin
from spyglass.common.common_task import Task
from spyglass.common.common_nwbfile import Nwbfile
from spyglass.utils.nwb_helper_fn import get_nwb_file

schema = dj.schema("task_leds")


@schema
class TaskLEDs(SpyglassMixin, dj.Imported):
    """Custom SpyGlass table for storing task LED configuration information.

    This table extends the standard SpyGlass Task table to include detailed
    information about LED configurations used in behavioral experiments.
    It stores individual LED names, their configurations, and spatial positions
    for each experimental task.

    The table inherits the primary key from the Task table and adds LED-specific
    attributes, enabling queries that link task parameters with LED setup details.
    """

    definition = """
    -> Task # Inherit primary key from Task
    led_name : varchar(32) # string of max length 32
    ---
    led_configuration : varchar(32) # string of max length 32
    led_position : varchar(32) # string of max length 32
    """

    def make(self, key):
        """Extract and populate LED configuration data from NWB file.

        Reads task information from the NWB file's processing module and extracts
        LED configuration details for each task. Parses comma-separated LED lists
        and positions to create individual table entries for each LED.

        Parameters
        ----------
        key : dict
            Dictionary containing the primary key, must include 'nwb_file_name'.

        Notes
        -----
        This method expects the NWB file to contain a 'tasks' processing module
        with task tables that include 'led_list', 'led_positions', and
        'led_configuration' columns. LED names and positions are parsed from
        comma-separated strings to create individual database entries.
        """

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
