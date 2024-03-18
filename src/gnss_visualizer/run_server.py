#!/usr/bin/env python3
"""Run the GNSS Visualizer application.


Wrapper for bokeh serve to run the GNSS Visualizer application.

This is alternative to running:
    bokeh serve src/gnss_visualizer --show --args INPUT
"""

import subprocess
from pathlib import Path

GNSS_VISUALIZER_PATH = Path(__file__).resolve().parent
import sys

from gnss_visualizer import app


def main():
    """Visualize GNSS data from INPUT file or device."""
    # use the same command line interface as the actual app
    app.handle_args()
    args = sys.argv[1:]
    cmd = ["bokeh", "serve", str(GNSS_VISUALIZER_PATH), "--show", "--args"] + args
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
