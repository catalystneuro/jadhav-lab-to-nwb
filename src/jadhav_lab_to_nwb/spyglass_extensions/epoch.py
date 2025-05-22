import datajoint as dj
from spyglass.utils import SpyglassMixin
from spyglass.common.common_task import TaskEpoch
from spyglass.common.common_nwbfile import Nwbfile
from spyglass.utils.nwb_helper_fn import get_nwb_file

schema = dj.schema("epoch")


@schema
class TaskLEDs(SpyglassMixin, dj.Imported):
    """Table to accompany spyglass.common.TaskEpoch with extra information about LEDs used in tasks."""

    definition = """
    -> TaskEpoch # Inherit primary key from TaskEpoch
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

        epochs = nwbf.epochs.to_dataframe()

        # Create a list of dictionaries to insert
        epoch_inserts = []
        for _, epoch_data in epochs.iterrows():
            epoch = int(epoch_data.tags[0])
            led_configuration = epoch_data.led_configuration
            led_names = epoch_data.led_list.split(",")
            led_positions = epoch_data.led_positions.split(",")
            for led_name, led_position in zip(led_names, led_positions):
                epoch_inserts.append(
                    {
                        "nwb_file_name": nwb_file_name,
                        "epoch": epoch,
                        "led_name": led_name,
                        "led_configuration": led_configuration,
                        "led_position": led_position,
                    }
                )
        self.insert(epoch_inserts, allow_direct_insert=True, skip_duplicates=True)
