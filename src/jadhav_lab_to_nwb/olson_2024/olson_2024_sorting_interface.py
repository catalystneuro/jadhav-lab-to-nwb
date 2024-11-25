"""Primary class for converting experiment-specific spike sorting."""
from pynwb.file import NWBFile
from pydantic import DirectoryPath
from neuroconv.basedatainterface import BaseDataInterface


class Olson2024SortingInterface(BaseDataInterface):
    """Sorting interface for olson_2024 conversion"""

    keywords = ("extracellular electrophysiology", "spike sorting")

    def __init__(self, folder_path: DirectoryPath):
        super().__init__(folder_path=folder_path)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        print("Olson2024SortingInterface.add_to_nwbfile")
