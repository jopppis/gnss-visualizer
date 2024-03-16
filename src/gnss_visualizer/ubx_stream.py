"""Read NMEA stream from a device."""

import io
import logging
from functools import partial
from pathlib import Path
from time import sleep

import pyubx2
from serial import Serial, SerialException

from gnss_visualizer.plot import PlotHandler

LOGGER = logging.getLogger(__name__)


class UbxStreamReader:
    def __init__(
        self,
        file: Path,
        plot_handler: PlotHandler,
        simulate_wait_s: float | None = None,
    ):
        self.file = file
        self.plot_handler = plot_handler
        self.simulate_wait_s = simulate_wait_s

    def read(self) -> None:
        """Read ubx from file or device."""
        if self.file.is_file():
            self._read_ubx_file()
            return

        self._read_ubx_device()

    def _read_ubx_file(self) -> None:
        """Read UBX from a file."""
        LOGGER.info(f"Reading UBX from file {self.file}")
        with self.file.open("rb") as f:
            self._read_ubx_stream(f)

    def _read_ubx_device(self) -> None:
        """Read UBX from a device."""
        LOGGER.info(f"Reading UBX from device {self.file}")

        # try reading from device few times
        while True:
            try:
                with Serial(str(self.file), 38400, timeout=3) as ser:
                    self._read_ubx_stream(ser)
            except SerialException as e:
                LOGGER.error(f"Serial exception: {e}")
                sleep(1)

    def _read_ubx_stream(self, stream: io.IOBase) -> None:
        """Read UBX stream from a stream."""
        ubr = pyubx2.UBXReader(stream, protfilter=pyubx2.UBX_PROTOCOL)
        while True:
            msg = ubr.read()[1]
            if msg is None:
                return
            # make sure the result is ubx
            if not isinstance(msg, pyubx2.UBXMessage):
                LOGGER.info(f"Message is not UBX: {msg}")
                continue

            # check the message type
            msg_str = pyubx2.UBX_MSGIDS[msg.msg_cls + msg.msg_id]
            if msg_str in self.plot_handler.required_msgs:
                self._read_msg(msg, msg_str)

            if (
                msg_str == "NAV-PVT"
                and self.simulate_wait_s is not None
                and self.file.is_file()
            ):
                LOGGER.info(f"Simulating wait of {self.simulate_wait_s} s")
                sleep(self.simulate_wait_s)

    def _read_msg(self, msg: pyubx2.UBXMessage, msg_str: str) -> None:
        """Read UBX message."""
        LOGGER.debug(f"Message: {msg_str}")
        for msg_handler in self.plot_handler.get_handlers_for_msg(msg_str):
            if msg_handler is not None:
                self.plot_handler.doc.add_next_tick_callback(
                    partial(msg_handler, msg=msg)
                )
