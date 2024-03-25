"""Read NMEA stream from a device."""

import io
import logging
from functools import partial
from pathlib import Path
from time import sleep

import pyubx2
from serial import Serial, SerialException

from gnss_visualizer.plot_handler import PlotHandler
from gnss_visualizer.protocols.ubx import get_full_ubx_msg_id

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
            msg_str = get_full_ubx_msg_id(msg)
            if msg_str in self.plot_handler.required_msgs:
                self._read_msg(msg, msg_str)

            if (
                msg_str == "UBX-NAV-PVT"
                and self.simulate_wait_s is not None
                and self.file.is_file()
            ):
                LOGGER.info(f"Simulating wait of {self.simulate_wait_s} s")
                sleep(self.simulate_wait_s)

    def _read_msg(self, msg: pyubx2.UBXMessage, msg_str: str) -> None:
        """Read UBX message."""
        LOGGER.debug(f"Message: {msg_str}")
        for plot in self.plot_handler.get_plots_for_msg(msg_str):
            self.plot_handler.doc.add_next_tick_callback(
                partial(self.plot_handler.update_plot, plot=plot, msg=msg)
            )
