"""Read UBX stream from a file or device."""

import io
import logging
from pathlib import Path
from threading import Lock
from time import sleep
from typing import Callable

import pyubx2
from serial import Serial, SerialException

from gnss_visualizer.protocols.ubx import get_full_ubx_msg_id

LOGGER = logging.getLogger(__name__)


class UbxStreamReader:
    def __init__(
        self,
        file: Path,
        process_msg_callback: Callable[[pyubx2.UBXMessage, str], None],
        get_required_msgs: Callable[[], set[str]],
        get_wait_time: Callable[[], float],
    ):
        self.file = file
        self.process_msg_callback = process_msg_callback
        self.get_required_msgs = get_required_msgs
        self.get_wait_time = get_wait_time

        # rewinding
        self._rewind_requested = False
        self.lock = Lock()

    def read(self, stop_on_serial_failure: bool = False) -> None:
        """Read ubx from file or device."""
        if self.file.is_file():
            self._read_ubx_file()
            return

        self._read_ubx_device(stop_on_serial_failure)

    def read_messages_of_type(self, msg_type: str) -> None:
        """Read UBX messages of a given type."""
        if not self.file.is_file():
            raise ValueError("Unable to read all messages from device")

        LOGGER.info(f"Reading UBX messages of type {msg_type} from file {self.file}")
        msgs = []
        with self.file.open("rb") as f:
            while (msg := self._read_ubx_message_from_file(f, msg_type)) is not None:
                msgs.append(msg)
        pass

    def rewind_file(self) -> None:
        """Rewind file to the beginning."""
        if not self.file.is_file():
            logging.warning(f"Unable to non file input {self.file}")
            return

        LOGGER.info(f"Requesting file {self.file} rewind")

        with self.lock:
            self._rewind_requested = True

    def _check_and_rewind_file_stream(self, stream: io.IOBase) -> None:
        """Rewind the file stream if requested.

        For serial devices the rewind is not possible so it is ignored.
        """
        if not self.file.is_file():
            return

        with self.lock:
            if self._rewind_requested:
                LOGGER.info("Rewinding the file.")
                stream.seek(0)
                self._rewind_requested = False

    def _read_ubx_message_from_file(
        self, stream: io.IOBase, msg_type: str
    ) -> pyubx2.UBXMessage:
        """Read UBX stream from a stream."""
        ubr = pyubx2.UBXReader(stream, protfilter=pyubx2.UBX_PROTOCOL)
        while True:
            msg = ubr.read()[1]
            if msg is None:
                return None
            # make sure the result is ubx
            if not isinstance(msg, pyubx2.UBXMessage):
                continue

            # check the message type
            msg_str = get_full_ubx_msg_id(msg)
            if msg_str != msg_type:
                continue

            return msg

    def _read_ubx_file(self) -> None:
        """Read UBX from a file."""
        LOGGER.info(f"Reading UBX from file {self.file}")
        with self.file.open("rb") as f:
            self._read_ubx_stream(f)

    def _read_ubx_device(self, stop_on_serial_failure: bool = False) -> None:
        """Read UBX from a device."""
        LOGGER.info(f"Reading UBX from device {self.file}")

        # try reading from device few times
        while True:
            try:
                with Serial(str(self.file), 38400, timeout=3) as ser:
                    self._read_ubx_stream(ser)
            except SerialException as e:
                LOGGER.error(f"Serial exception: {e}")
                if stop_on_serial_failure:
                    raise e
                sleep(1)

    def _read_ubx_stream(self, stream: io.IOBase) -> None:
        """Read UBX stream from a stream."""
        ubr = pyubx2.UBXReader(stream, protfilter=pyubx2.UBX_PROTOCOL)
        while True:
            if self.file.is_file():
                # yield some time to other threads when reading files
                sleep(0.01)
                # rewind if requested
                self._check_and_rewind_file_stream(stream)

            msg = ubr.read()[1]

            if msg is None:
                # stream ended
                return

            if not isinstance(msg, pyubx2.UBXMessage):
                LOGGER.info(f"Message is not UBX: {msg}")
                continue

            msg_str = get_full_ubx_msg_id(msg)
            if msg_str in self.get_required_msgs():
                self.process_msg_callback(msg, msg_str)

            if msg_str == "UBX-NAV-PVT" and self.file.is_file():
                wait_time = self.get_wait_time()
                if wait_time:
                    LOGGER.info(f"Simulating wait of {wait_time} s")
                    sleep(wait_time)
