"""C/N0 plots for GNSS Visualizer."""

import gettext
import locale
import logging
from pathlib import Path
from typing import Any, Iterable

import pyubx2
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from gnss_visualizer.constants import RINEX_CONSTELLATION_COLORS, UBX_GNSSID_TO_RINEX
from gnss_visualizer.plots.generic_plot import GenericContinuousPlot

locale.setlocale(locale.LC_ALL, "")
lang = gettext.translation(
    "messages", localedir=Path(__file__).parent.parent / "translations", fallback=True
)
lang.install()
_ = lang.gettext

LOGGER = logging.getLogger(__name__)


class LiveSVCnoPlot(GenericContinuousPlot):
    """Live plot for C/N0 values.

    Plots the C/N0 for the strongest signal for each SV.
    """

    @property
    def name(self) -> str:
        """Get the name of the plot."""
        return _("Signal strength (live)")

    @property
    def required_messages(self) -> list[str]:
        """Get required messages for this plot."""
        return ["UBX-NAV-SIG"]

    def update_plot(self, msg: pyubx2.UBXMessage) -> None:
        """Update the plot."""
        LOGGER.info("Update SV C/N0 plot")

        # make dict of the SV C/N0 values
        cnos: dict[str, int] = {}
        for ix in range(1, msg.numSigs + 1):
            gnss_id = getattr(msg, f"gnssId_{ix:02}")
            sv_id = getattr(msg, f"svId_{ix:02}")
            cno = getattr(msg, f"cno_{ix:02}")

            if cno:
                rinex_sv_id = f"{UBX_GNSSID_TO_RINEX[gnss_id]}{sv_id}"
                if rinex_sv_id not in cnos or cno > cnos[rinex_sv_id]:
                    cnos[rinex_sv_id] = cno

        # convert to dict suitable for column data source
        data: dict[str, list[Any]] = {
            "x": list(cnos.keys()),
            "y": list(cnos.values()),
        }

        # add colors
        data["color"] = [RINEX_CONSTELLATION_COLORS[sv_id[0]] for sv_id in data["x"]]

        if self.figure is None or self.datasource is None:
            self.init_plot(ColumnDataSource(data=data))
        else:
            self.datasource.data = data
            self.figure.x_range.factors = self._sort_rinex_sv_ids(
                set(list(self.figure.x_range.factors) + data["x"])
            )

    def init_plot(self, datasource: ColumnDataSource) -> None:
        """Initialize the plot."""
        LOGGER.info("Initialize continuous SV C/N0 plot")
        y_label = "C/N0 [dBHz]"
        x_label = _("Satellite")

        tooltip = [
            (x_label, "@x"),
            (y_label, "@y"),
        ]

        self.datasource = datasource
        self.figure = figure(
            height=self.DEFAULT_PLOT_HEIGHT,
            title=_("Signal strength"),
            tools=self.DEFAULT_TOOLS,
            tooltips=tooltip,
            x_range=self._sort_rinex_sv_ids(self.datasource.data["x"]),
            sizing_mode="inherit",
        )

        self.figure.vbar(
            x="x", top="y", source=self.datasource, width=0.9, color="color"
        )

        self.figure.y_range.start = 0
        self.figure.y_range.end = 64
        self.figure.xaxis.major_label_orientation = 3.14 / 4

        self.figure.yaxis.axis_label = y_label
        self.figure.xaxis.axis_label = x_label

        self._finalize_figure()

    def _sort_rinex_sv_ids(self, rinex_sv_ids: Iterable[str]) -> list[str]:
        def constellation_sort(item: str) -> tuple[int, int]:
            if item.startswith("G"):
                return (0, int(item[1:]))
            elif item.startswith("E"):
                return (1, int(item[1:]))
            elif item.startswith("C"):
                return (2, int(item[1:]))
            elif item.startswith("R"):
                return (3, int(item[1:]))
            elif item.startswith("S"):
                return (4, int(item[1:]))
            elif item.startswith("J"):
                return (5, int(item[1:]))
            else:
                return (6, int(item[1:]))

        return sorted(rinex_sv_ids, key=constellation_sort)
