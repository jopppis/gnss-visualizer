"""Configure unit tests."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import pyubx2


@pytest.fixture
def nav_pvt_message_bytes() -> bytes:
    """Generate a valid UBX-NAV-PVT message."""
    return b"\xb5b\x01\x07\\\x00\x00\x00\x00\x00\xe5\x07\x0c\x0c\x00\x00\x00\xf0\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00$\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x98\xbd\xff\xff\xff\xff\xff\xff\x00v\x84\xdf\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 N\x00\x00\x80\xa8\x12\x01\x0f'\x00\x00\"\x9eE3\x00\x00\x00\x00\x00\x00\x00\x00\xb7\x8e"


@pytest.fixture
def nav_pvt_message(nav_pvt_message_bytes: bytes) -> pyubx2.UBXMessage:
    """Generate a valid UBX-NAV-PVT message."""
    return pyubx2.UBXReader.parse(nav_pvt_message_bytes)


@pytest.fixture
def nav_pvt_message_file(nav_pvt_message_bytes: bytes) -> Path:
    """Generate a file with a UBX-NAV-PVT message."""
    with NamedTemporaryFile(delete=False) as file:
        file.write(nav_pvt_message_bytes)
        return Path(file.name)
