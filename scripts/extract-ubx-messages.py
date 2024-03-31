#!/usr/bin/env python3
"""Extract ubx messages from a file.

This tool can be used to extract certain ubx messages from a file e.g. for unit
tests.

The messages are output as raw byte strings.

Example usage to get the first two NAV-PVT messages from a file:
scripts/extract-ubx-messages.py coldstart.ubx NAV-PVT -n 2
"""

import argparse
import logging
from pathlib import Path

import pyubx2


def handle_args() -> argparse.Namespace:
    """Handle command-line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Input file")
    parser.add_argument(
        "message_type", type=str, help="Message type to extract, e.g. NAV-PVT"
    )
    parser.add_argument(
        "-n",
        "--num-messages",
        type=int,
        default=1,
        help="Number of messages to extract",
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
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=level,
    )

    return args


def extract_messages(input_file: Path, msg_type: str, num_messages: int) -> None:
    """Extract messages from a file."""
    logging.info(
        f"Extracting {num_messages} messages of type {msg_type} from {input_file}"
    )
    with open(input_file, "rb") as f:
        ubr = pyubx2.UBXReader(f, protfilter=pyubx2.UBX_PROTOCOL)
        while True:
            msg = ubr.read()[1]
            if msg is None:
                logging.debug("End of file")
                return
            # make sure the result is ubx
            if not isinstance(msg, pyubx2.UBXMessage):
                logging.debug(f"Message is not UBX: {msg}")
                continue

            # check the message type
            if msg.identity != msg_type:
                return

            print(msg.serialize())


def main() -> None:
    """Main entry point for the script."""
    args = handle_args()
    extract_messages(args.input, args.message_type, args.num_messages)


if __name__ == "__main__":
    main()
#
