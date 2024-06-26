#!/usr/bin/env python3
"""GNSS Visualizer application.

Visualization tool for GNSS data. Reads UBX messages from a file or device and
generates plots from the data.
"""

import argparse
import logging
from pathlib import Path

from gnss_visualizer.ubx_stream import LOGGER as ubx_logger
from gnss_visualizer.ui_handler import LOGGER as plot_logger
from gnss_visualizer.ui_handler import UIHandler

LOGGER = logging.getLogger(__name__)


def handle_args() -> argparse.Namespace:
    """Handle command-line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Input file or device.")
    parser.add_argument(
        "-w",
        "--default-simulate-wait-s",
        type=float,
        default=0.1,
        help="Default value for simulated wait time between NAV-PVT messages, only applies for reading files.",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Enable live reloading during app development.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Produce verbose output. Use multiple times to increase verbosity.",
    )

    args = parser.parse_args()

    # set logging
    if args.verbose == 1:
        level = logging.INFO
    elif args.verbose > 1:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(
        level=level,
    )
    for logger in (LOGGER, plot_logger, ubx_logger):
        logger.setLevel(level)

    return args


def run_app(args: argparse.Namespace) -> None:
    """Start the application.

    This is meant to be called from bokeh server.
    """
    LOGGER.info("Starting GNSS Visualizer application.")

    UIHandler(args.input, args.default_simulate_wait_s)
