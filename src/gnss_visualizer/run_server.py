#!/usr/bin/env python3
"""Run the GNSS Visualizer application.


Wrapper for bokeh serve to run the GNSS Visualizer application.

This is alternative to running:
    bokeh serve src/gnss_visualizer --show --args INPUT
"""

import subprocess
import sys
from pathlib import Path

from gnss_visualizer import app

GNSS_VISUALIZER_PATH = Path(__file__).resolve().parent


def main():
    """Visualize GNSS data from INPUT file or device."""
    # use the same command line interface as the actual app
    parsed_args = app.handle_args()
    # run the bokeh serve command with the same python interpreter
    cmd = [
        sys.executable,
        "-m",
        "bokeh",
        "serve",
    ]
    if parsed_args.dev:
        cmd.append("--dev")
    cmd += [
        "--show",
        str(GNSS_VISUALIZER_PATH),
        "--args",
    ] + sys.argv[1:]

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
