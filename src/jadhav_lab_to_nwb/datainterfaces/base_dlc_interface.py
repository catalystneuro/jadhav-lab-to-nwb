"""Base interface for converting DeepLabCut pose estimation data to NWB format.

This module provides the foundational interface for integrating DeepLabCut pose estimation
data into the neuroscience data conversion pipeline. It serves as an abstract base class
that handles multiple DeepLabCut output files (.h5 or .csv) containing pose tracking results.
"""
from abc import abstractmethod
from pynwb.file import NWBFile
from pydantic import FilePath

from neuroconv.utils import DeepDict, dict_deep_update
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import DeepLabCutInterface


class BaseDeepLabCutInterface(BaseDataInterface):
    """Base interface for converting DeepLabCut pose estimation data to NWB format.

    This abstract base class provides the core functionality for handling DeepLabCut
    pose estimation output files (.h5 or .csv) across multiple experimental epochs.

    Notes
    -----
    This is an abstract base class that requires implementation of several methods:
    - get_subject_name: Extract subject name from file names
    - get_pose_estimation_metadata_key: Generate metadata keys for pose estimation
    - get_task_name: Determine task name for each pose estimation file
    """

    keywords = ("DLC",)

    def __init__(
        self,
        file_paths: list[list[FilePath] | FilePath],
        config_file_paths: list[list[FilePath] | FilePath] | None = None,
        subject_id: str | None = None,
        verbose: bool = True,
    ):
        """Initialize the BaseDeepLabCutInterface.

        Sets up individual DeepLabCutInterface objects for each pose estimation file,
        handling the mapping between pose estimation files and their corresponding
        configuration files. This method processes nested file structures to support
        multi-segment, multi-epoch experiments and ensures proper pairing of data and config files.

        Parameters
        ----------
        file_paths : list[list[FilePath] | FilePath]
            List of file paths to DeepLabCut output files (.h5 or .csv format).
            Can be nested lists for multiple epochs, where each epoch can have
            multiple pose estimation files. Files must be sorted in the order
            that the corresponding videos were recorded. Single files will be
            automatically converted to single-element lists.
        config_file_paths : list[list[FilePath] | FilePath] | None, optional
            List of paths to DeepLabCut config files corresponding to each pose
            estimation file. If None, config files are assumed to be None for all files.
            Must match the structure of file_paths (same nesting and length).
            Each config file contains the DeepLabCut project configuration including
            bodypart definitions and model parameters.
        subject_id : str | None, optional
            Identifier for the experimental subject. Used in generating subject-specific
            metadata keys and names. If provided, will be passed to abstract methods
            for customized subject name and metadata key generation.
        verbose : bool, default True
            Whether to print verbose output during processing. Enables detailed
            logging of interface creation and file processing steps.

        Raises
        ------
        AssertionError
            If file_paths is empty or if the number of file paths doesn't match
            the number of config file paths.
        """
        # file_paths must be sorted in the order that the videos were recorded
        assert len(file_paths) > 0, "At least one file path must be provided."
        if config_file_paths is None:
            config_file_paths = [[None] * len(fp) if isinstance(fp, list) else None for fp in file_paths]
        msg = "The number of file paths must match the number of config file paths."
        assert len(file_paths) == len(config_file_paths), msg
        dlc_interfaces = []
        for epoch_file_paths, epoch_config_file_paths in zip(file_paths, config_file_paths):
            if not isinstance(epoch_file_paths, list):
                epoch_file_paths = [epoch_file_paths]
            if not isinstance(epoch_config_file_paths, list):
                epoch_config_file_paths = [epoch_config_file_paths]
            assert len(epoch_file_paths) == len(epoch_config_file_paths), msg
            for file_path, config_file_path in zip(epoch_file_paths, epoch_config_file_paths):
                subject_name = self.get_subject_name(file_name=file_path.name, subject_id=subject_id)
                pose_estimation_metadata_key = self.get_pose_estimation_metadata_key(
                    file_name=file_path.name, subject_id=subject_id
                )
                dlc_interface = DeepLabCutInterface(
                    file_path=file_path,
                    config_file_path=config_file_path,
                    subject_name=subject_name,
                    pose_estimation_metadata_key=pose_estimation_metadata_key,
                    verbose=verbose,
                )
                dlc_interfaces.append(dlc_interface)
        self.dlc_interfaces = dlc_interfaces

    @abstractmethod
    def get_subject_name(self, file_name: str, subject_id: str | None = None) -> str:
        """Extract subject name from file name.

        This method must be implemented by subclasses to define how subject names
        are parsed from DeepLabCut output file names. The subject name is used
        in NWB metadata and for organizing pose estimation data.

        Parameters
        ----------
        file_name : str
            Name of the DeepLabCut output file.
        subject_id : str | None, optional
            Optional subject identifier that can be used in name generation.

        Returns
        -------
        str
            The extracted or generated subject name.
        """
        pass

    @abstractmethod
    def get_pose_estimation_metadata_key(self, file_name: str, subject_id: str | None = None) -> str:
        """Generate metadata key for pose estimation container.

        This method must be implemented by subclasses to define how metadata keys
        are generated for pose estimation containers in the NWB file. These keys
        are used to organize and reference pose estimation data.

        Parameters
        ----------
        file_name : str
            Name of the DeepLabCut output file.
        subject_id : str | None, optional
            Optional subject identifier for key generation.

        Returns
        -------
        str
            The generated metadata key for the pose estimation container.
        """
        pass

    @abstractmethod
    def get_task_name(self, dlc_interface: DeepLabCutInterface) -> str:
        """Determine task name for a DeepLabCut interface.

        This method must be implemented by subclasses to define how task names
        are determined from DeepLabCut interfaces. Task names are used to link
        pose estimation data with corresponding behavioral tasks and video data.

        Parameters
        ----------
        dlc_interface : DeepLabCutInterface
            The DeepLabCut interface object to extract task name from.

        Returns
        -------
        str
            The task name associated with this pose estimation data.
        """
        pass

    def get_metadata(self) -> DeepDict:
        """Aggregate metadata from all DeepLabCut interfaces.

        Collects and merges metadata from all individual DeepLabCut interfaces
        managed by this base interface. This includes pose estimation parameters,
        subject information, and device configurations.

        Returns
        -------
        DeepDict
            Merged metadata dictionary containing all pose estimation metadata.
        """
        metadata = super().get_metadata()
        for dlc_interface in self.dlc_interfaces:
            interface_metadata = dlc_interface.get_metadata()
            dict_deep_update(metadata, interface_metadata)
        return metadata

    def get_metadata_schema(self) -> DeepDict:
        """Aggregate metadata schema from all DeepLabCut interfaces.

        Collects and merges metadata schemas from all individual DeepLabCut
        interfaces to provide a comprehensive schema for validation.

        Returns
        -------
        DeepDict
            Merged metadata schema dictionary.
        """
        metadata_schema = super().get_metadata_schema()
        for dlc_interface in self.dlc_interfaces:
            metadata_schema = dict_deep_update(metadata_schema, dlc_interface.get_metadata_schema())
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        """Add pose estimation data to NWB file.

        Processes all DeepLabCut interfaces and adds their pose estimation data
        to the NWB file. This method handles the coordination between video devices
        and pose estimation containers, ensuring proper metadata linkage.

        For each DeepLabCut interface, this method:
        1. Determines the associated task and camera device
        2. Updates metadata to link camera devices with pose estimation containers
        3. Adds the pose estimation data to the NWB file

        Parameters
        ----------
        nwbfile : NWBFile
            The NWB file object to add pose estimation data to.
        metadata : dict
            Metadata dictionary containing task information, device configurations,
            and pose estimation parameters.

        Notes
        -----
        This method modifies the metadata dictionary to establish proper device
        linkages between video cameras and pose estimation containers.
        """
        for dlc_interface in self.dlc_interfaces:
            # Update the metadata to connect camera_device from Video to PoseEstimation
            pem_key = dlc_interface.pose_estimation_metadata_key
            task_name = self.get_task_name(dlc_interface=dlc_interface)
            task_metadata = next(meta for meta in metadata["Tasks"] if meta["name"] == task_name)
            camera_id = task_metadata["camera_id"][0]
            device_name = f"camera_device {camera_id}"
            metadata["PoseEstimation"]["PoseEstimationContainers"][pem_key]["devices"] = [device_name]
            metadata["PoseEstimation"]["Devices"][device_name] = dict(name=device_name)

            dlc_interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)
