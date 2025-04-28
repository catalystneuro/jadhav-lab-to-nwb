"""Primary class for converting experiment-specific behavioral video."""
from pynwb.file import NWBFile
from pynwb.behavior import BehavioralEvents
from pydantic import FilePath
import re

from neuroconv.utils import DeepDict, dict_deep_update
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import VideoInterface
from neuroconv.utils import get_base_schema
from ndx_franklab_novela import CameraDevice

from .tools.spikegadgets import readCameraModuleTimeStamps
from .utils.utils import get_epoch_name


class RiveraAndShukla2025VideoInterface(BaseDataInterface):
    """Video interface for rivera_and_shukla_2025 conversion"""

    keywords = ("movie", "natural behavior", "tracking")

    def __init__(self, file_paths: list[FilePath], video_timestamps_file_paths: list[FilePath]):
        # file_paths must be sorted in the order that the videos were recorded
        assert len(file_paths) > 0, "At least one file path must be provided."
        assert len(file_paths) == len(
            video_timestamps_file_paths
        ), "The number of file paths must match the number of video timestamps file paths."
        video_interfaces = []
        for file_path, video_timestamps_file_path in zip(file_paths, video_timestamps_file_paths):
            epoch_name = get_epoch_name(name=file_path.parent.name)
            metadata_key_name = "Video" + "_" + epoch_name  # TODO: Document this naming convention in the docstring
            video_interface = SpyglassVideoInterface(file_paths=[file_path], metadata_key_name=metadata_key_name)
            timestamps, _ = readCameraModuleTimeStamps(video_timestamps_file_path)
            video_interface.set_aligned_timestamps(aligned_timestamps=[timestamps])
            video_interfaces.append(video_interface)
        self.video_interfaces = video_interfaces

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        for video_interface in self.video_interfaces:
            metadata = dict_deep_update(metadata, video_interface.get_metadata())
        return metadata

    def get_metadata_schema(self) -> DeepDict:
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Behavior"] = get_base_schema(tag="Behavior")
        metadata_schema["properties"]["Behavior"]["properties"]["Video"] = {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "General description of the video recording setup and purpose",
                },
                "CameraDevice": {
                    "description": "Metadata for each camera device, compatible with spyglass",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Unique identifier for the camera device. Must be formatted as 'camera_device <id>'.",
                            },
                            "meters_per_pixel": {
                                "type": "number",
                                "description": "Spatial resolution of the camera in meters per pixel",
                            },
                            "manufacturer": {"type": "string", "description": "Name of the camera manufacturer"},
                            "model": {"type": "string", "description": "Model number or name of the camera"},
                            "lens": {"type": "string", "description": "Specifications of the camera lens"},
                            "camera_name": {
                                "type": "string",
                                "description": "Common name or label used for the camera",
                            },
                        },
                        "required": ["name", "meters_per_pixel", "manufacturer", "model", "lens", "camera_name"],
                    },
                },
            },
            "required": ["description", "CameraDevice"],
        }
        for video_interface in self.video_interfaces:
            metadata_schema = dict_deep_update(metadata_schema, video_interface.get_metadata_schema())
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        for camera_device_metadata in metadata["Behavior"]["Video"]["CameraDevice"]:
            camera_device = CameraDevice(
                name=camera_device_metadata["name"],
                meters_per_pixel=camera_device_metadata["meters_per_pixel"],
                model=camera_device_metadata["model"],
                lens=camera_device_metadata["lens"],
                camera_name=camera_device_metadata["camera_name"],
            )
            nwbfile.add_device(camera_device)
        video_description = metadata["Behavior"]["Video"]["description"]
        for video_interface in self.video_interfaces:
            session_id = re.search("S[0-9][0-9]", video_interface.metadata_key_name).group(0)
            task_epoch = int(session_id[1:])
            task_metadata = next(meta for meta in metadata["Tasks"] if task_epoch in meta["task_epochs"])
            camera_id = task_metadata["camera_id"][0]
            device_name = f"camera_device {camera_id}"
            metadata["Behavior"][video_interface.metadata_key_name][0]["description"] = video_description
            video_interface.add_to_nwbfile(
                nwbfile=nwbfile, metadata=metadata, module_name="behavior", device_name=device_name
            )


import warnings
from copy import deepcopy
from pathlib import Path
from typing import Optional

import numpy as np
import psutil
from hdmf.data_utils import DataChunkIterator
from pydantic import FilePath
from pynwb import NWBFile
from pynwb.image import ImageSeries
from tqdm import tqdm

from neuroconv.datainterfaces.behavior.video.video_utils import VideoCaptureContext
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.tools.nwb_helpers import get_module
from neuroconv.utils.str_utils import human_readable_size


class SpyglassVideoInterface(VideoInterface):
    """Video interface for spyglass conversion

    This class is identical to VideoInterface, but changes the way the ImageSeries is added to the nwbfile, so that
    it is compatible with the spyglass pipeline. It also adds a device_name argument to the add_to_nwbfile method to
    specify the name of the CameraDevice in the NWBFile.
    """

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        stub_test: bool = False,
        external_mode: bool = True,
        starting_frames: Optional[list[int]] = None,
        chunk_data: bool = True,
        module_name: Optional[str] = None,
        module_description: Optional[str] = None,
        device_name: Optional[str] = None,
    ):
        metadata = metadata or dict()

        file_paths = self.source_data["file_paths"]

        # Be sure to copy metadata at this step to avoid mutating in-place
        videos_metadata = deepcopy(metadata).get("Behavior", dict()).get(self.metadata_key_name, None)
        if videos_metadata is None:
            videos_metadata = deepcopy(self.get_metadata()["Behavior"][self.metadata_key_name])

        assert len(videos_metadata) == self._number_of_files, (
            "Incomplete metadata "
            f"(number of metadata in video {len(videos_metadata)})"
            f"is not equal to the number of file_paths {self._number_of_files}"
        )

        videos_name_list = [video["name"] for video in videos_metadata]
        any_duplicated_video_names = len(set(videos_name_list)) < len(videos_name_list)
        if any_duplicated_video_names:
            raise ValueError("There are duplicated file names in the metadata!")

        # Iterate over unique videos
        stub_frames = 10
        timing_type = self.get_timing_type()
        if external_mode:
            image_series_kwargs = videos_metadata[0]
            if self._number_of_files > 1 and starting_frames is None:
                raise TypeError(
                    "Multiple paths were specified for the ImageSeries, but no starting_frames were specified!"
                )
            elif starting_frames is not None and len(starting_frames) != self._number_of_files:
                raise ValueError(
                    f"Multiple paths ({self._number_of_files}) were specified for the ImageSeries, "
                    f"but the length of starting_frames ({len(starting_frames)}) did not match the number of paths!"
                )
            elif starting_frames is not None:
                image_series_kwargs.update(starting_frame=starting_frames)

            image_series_kwargs.update(format="external", external_file=file_paths)

            if timing_type == "starting_time and rate":
                starting_time = self._segment_starting_times[0] if self._segment_starting_times is not None else 0.0
                with VideoCaptureContext(file_path=str(file_paths[0])) as video:
                    rate = video.get_video_fps()
                image_series_kwargs.update(starting_time=starting_time, rate=rate)
            elif timing_type == "timestamps":
                image_series_kwargs.update(timestamps=np.concatenate(self._timestamps))
            else:
                raise ValueError(f"Unrecognized timing_type: {timing_type}")
        else:
            for file_index, (image_series_kwargs, file) in enumerate(zip(videos_metadata, file_paths)):
                if self._number_of_files > 1:
                    raise NotImplementedError(
                        "Multiple file_paths with external_mode=False is not yet supported! "
                        "Please initialize a separate VideoInterface for each file."
                    )

                uncompressed_estimate = Path(file).stat().st_size * 70
                available_memory = psutil.virtual_memory().available
                if not chunk_data and not stub_test and uncompressed_estimate >= available_memory:
                    warnings.warn(
                        f"Not enough memory (estimated {human_readable_size(uncompressed_estimate)}) to load video file"
                        f"as array ({human_readable_size(available_memory)} available)! Forcing chunk_data to True."
                    )
                    chunk_data = True
                with VideoCaptureContext(str(file)) as video_capture_ob:
                    if stub_test:
                        video_capture_ob.frame_count = stub_frames
                    total_frames = video_capture_ob.get_video_frame_count()
                    frame_shape = video_capture_ob.get_frame_shape()

                maxshape = (total_frames, *frame_shape)
                tqdm_pos, tqdm_mininterval = (0, 10)

                if chunk_data:
                    chunks = (1, frame_shape[0], frame_shape[1], 3)  # best_gzip_chunk
                    video_capture_ob = VideoCaptureContext(str(file))
                    if stub_test:
                        video_capture_ob.frame_count = stub_frames
                    iterable = DataChunkIterator(
                        data=tqdm(
                            iterable=video_capture_ob,
                            desc=f"Copying video data for {Path(file).name}",
                            position=tqdm_pos,
                            total=total_frames,
                            mininterval=tqdm_mininterval,
                        ),
                        iter_axis=0,  # nwb standard is time as zero axis
                        maxshape=maxshape,
                    )

                else:
                    # Load the video
                    chunks = None
                    video = np.zeros(shape=maxshape, dtype="uint8")
                    with VideoCaptureContext(str(file)) as video_capture_ob:
                        if stub_test:
                            video_capture_ob.frame_count = stub_frames
                        with tqdm(
                            desc=f"Reading video data for {Path(file).name}",
                            position=tqdm_pos,
                            total=total_frames,
                            mininterval=tqdm_mininterval,
                        ) as pbar:
                            for n, frame in enumerate(video_capture_ob):
                                video[n, :, :, :] = frame
                                pbar.update(1)
                    iterable = video

                image_series_kwargs.update(data=iterable)

                if timing_type == "starting_time and rate":
                    starting_time = (
                        self._segment_starting_times[file_index] if self._segment_starting_times is not None else 0.0
                    )
                    with VideoCaptureContext(file_path=str(file)) as video:
                        rate = video.get_video_fps()
                    image_series_kwargs.update(starting_time=starting_time, rate=rate)
                elif timing_type == "timestamps":
                    image_series_kwargs.update(timestamps=self._timestamps[file_index])

        # Attach image series -- NOT IDENTICAL TO VideoInterface --
        if device_name is not None:
            camera_device = nwbfile.devices[device_name]
            image_series_kwargs.update(device=camera_device)
        image_series = ImageSeries(**image_series_kwargs)
        module = get_module(nwbfile=nwbfile, name=module_name, description=module_description)
        if "video" in module.data_interfaces:
            behavioral_events = module.data_interfaces["video"]
            behavioral_events.add_timeseries(image_series)
        else:
            behavioral_events = BehavioralEvents(name="video")
            behavioral_events.add_timeseries(image_series)
            module.add(behavioral_events)

        return nwbfile
