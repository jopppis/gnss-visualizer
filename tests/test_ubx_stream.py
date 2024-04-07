"""Unit tests for ubx_stream.py."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pyubx2
from gnss_visualizer.ubx_stream import UbxStreamReader
from serial import SerialException


@pytest.fixture
def ubx_stream_reader(nav_pvt_message_file: Path) -> UbxStreamReader:
    """Fixture to create a UbxStreamReader instance with mocked dependencies."""
    process_msg_callback = MagicMock()
    get_required_msgs = MagicMock(return_value={"UBX-NAV-PVT"})
    get_wait_time = MagicMock(return_value=0.1)
    reader = UbxStreamReader(
        nav_pvt_message_file, process_msg_callback, get_required_msgs, get_wait_time
    )
    return reader


def test_initialization(ubx_stream_reader: UbxStreamReader) -> None:
    """Make sure the UbxStreamReader is correctly initialized."""
    assert ubx_stream_reader.file.exists()


def test_read_messages_of_type_file_not_found(
    ubx_stream_reader: UbxStreamReader,
) -> None:
    """Make sure an exception is raised when the file does not exist."""
    process_msg_callback = MagicMock()
    get_required_msgs = MagicMock(return_value={"UBX-NAV-PVT"})
    get_wait_time = MagicMock(return_value=0.1)
    reader = UbxStreamReader(
        Path("/home/morgoth/secret/path/to/nonexistent/file/69"),
        process_msg_callback,
        get_required_msgs,
        get_wait_time,
    )

    with pytest.raises(ValueError):
        reader.read_messages_of_type("UBX-NAV-PVT")


def test_callback_invocation(
    ubx_stream_reader: UbxStreamReader, nav_pvt_message_bytes: bytes
) -> None:
    """Test if the callback function is correctly invoked with the expected message."""
    ubx_stream_reader.read()
    ubx_stream_reader.process_msg_callback.assert_called_once()  # type: ignore[attr-defined]
    # check that process_msg callback had the expected arguments
    msg: pyubx2.UBXMessage = ubx_stream_reader.process_msg_callback.call_args[0][0]  # type: ignore[attr-defined]
    msg_str = ubx_stream_reader.process_msg_callback.call_args[0][1]  # type: ignore[attr-defined]
    assert msg.serialize() == nav_pvt_message_bytes
    assert msg_str == "UBX-NAV-PVT"


def test_rewind_file_stream(ubx_stream_reader: UbxStreamReader) -> None:
    """Test if the file stream is rewound when the end is reached."""
    assert not ubx_stream_reader._rewind_requested
    ubx_stream_reader.rewind_file()
    assert ubx_stream_reader._rewind_requested
    ubx_stream_reader.read()
    assert not ubx_stream_reader._rewind_requested
    ubx_stream_reader.rewind_file()
    assert ubx_stream_reader._rewind_requested


def test_read_device_nonexistent(nav_pvt_message_bytes: bytes) -> None:
    """Test if the read_device method reads from the device."""
    ubx_stream_reader = UbxStreamReader(
        Path("/dev/ttyUSB69"),
        MagicMock(),
        MagicMock(return_value={"UBX-NAV-PVT"}),
        MagicMock(return_value=0.1),
    )

    with pytest.raises(SerialException):
        ubx_stream_reader.read(stop_on_serial_failure=True)
