"""The raw signal's times come from the .rec packet timestamps (issue #23)."""

from pathlib import Path

import numpy as np
import pytest
from spikeinterface.extractors import SpikeGadgetsRecordingExtractor

from jadhav_lab_to_nwb.tools.spikegadgets import get_rec_timestamps

SAMPLING_RATE = 30000
HEADER = """<?xml version="1.0"?>
<Configuration>
 <GlobalConfiguration trodesVersion="2.3.4" headstageSerial="00000" controllerFirmwareVersion="0" headstageFirmwareVersion="0" timestampAtCreation="0" systemTimeAtCreation="0"/>
 <HardwareConfiguration samplingRate="{rate}" numChannels="4">
  <Device name="MCU" numBytes="2" available="1" packetOrderPreference="10">
   <Channel id="MCU_Din1" dataType="digital" startByte="0" bit="0" input="1"/>
  </Device>
 </HardwareConfiguration>
 <SpikeConfiguration device="intan" chanPerChip="4" categories="">
  <SpikeNTrode id="1" LFPChan="1" spikeScalingToUv="0.195" refNTrodeID="1" refChan="1">
   <SpikeChannel hwChan="0" maxDisp="400" thresh="60" triggerOn="1"/>
   <SpikeChannel hwChan="1" maxDisp="400" thresh="60" triggerOn="1"/>
   <SpikeChannel hwChan="2" maxDisp="400" thresh="60" triggerOn="1"/>
   <SpikeChannel hwChan="3" maxDisp="400" thresh="60" triggerOn="1"/>
  </SpikeNTrode>
 </SpikeConfiguration>
</Configuration>
"""


def write_rec(path: Path, counts: np.ndarray, n_channels: int = 4) -> None:
    """A minimal .rec: the XML header, then one packet per sample (sync byte, MCU bytes, uint32 count, int16s)."""
    packets = np.zeros(
        len(counts), dtype=[("sync", "u1"), ("mcu", "u1", 2), ("count", "<u4"), ("data", "<i2", n_channels)]
    )
    packets["sync"] = 0x55
    packets["count"] = counts
    packets["data"] = np.arange(len(counts) * n_channels, dtype=np.int16).reshape(len(counts), n_channels)
    with open(path, "wb") as f:
        f.write(HEADER.format(rate=SAMPLING_RATE).encode("utf8"))
        f.write(packets.tobytes())


def test_times_follow_the_packet_counts(tmp_path):
    # A recording that starts at clock count 123,456 and pauses for 3 s after 1,000 samples
    counts = np.r_[123_456 + np.arange(1000), 123_456 + 1000 + 3 * SAMPLING_RATE + np.arange(500)].astype(np.uint32)
    path = tmp_path / "test.rec"
    write_rec(path, counts)
    recording = SpikeGadgetsRecordingExtractor(file_path=path, stream_id="trodes")
    times = get_rec_timestamps(recording)
    np.testing.assert_allclose(times, counts / SAMPLING_RATE)
    assert times[0] == pytest.approx(123_456 / SAMPLING_RATE)
    assert times[1000] - times[999] == pytest.approx(3 + 1 / SAMPLING_RATE)
    # Set on the recording, the times survive a frame slice (stub tests use one)
    recording.set_times(times)
    np.testing.assert_allclose(recording.frame_slice(990, 1010).get_times(), times[990:1010])


def test_decreasing_counts_are_refused(tmp_path):
    path = tmp_path / "test.rec"
    write_rec(path, np.array([10, 11, 12, 5, 6], dtype=np.uint32))
    recording = SpikeGadgetsRecordingExtractor(file_path=path, stream_id="trodes")
    with pytest.raises(ValueError, match="not strictly increasing"):
        get_rec_timestamps(recording)
