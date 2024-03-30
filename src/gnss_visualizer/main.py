#!/usr/bin/env python3
"""Entry point for bokeh server application."""

from gnss_visualizer import app


def main() -> None:
    """Visualize GNSS data from INPUT file or device."""
    args = app.handle_args()

    app.run_app(args)


main()
