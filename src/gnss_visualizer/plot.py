"""Generate plots."""

import logging
from typing import Any, Callable, Iterable

import pyubx2
import xyzservices.providers as xyz
from bokeh.document import Document
from bokeh.layouts import Spacer, column
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from gnss_visualizer.constants import RINEX_CONSTELLATION_COLORS, UBX_GNSSID_TO_RINEX
from gnss_visualizer.conversions import lat_lon_to_web_mercator
from gnss_visualizer.models.plot import Plot

LOGGER = logging.getLogger(__name__)


class PlotHandler:
    """Generate plots from GNSS receiver messages."""

    DEFAULT_PLOT_WIDTH = 1200
    DEFAULT_PLOT_HEIGHT = 500
    MAP_PLOT_HEIGHT = 400
    SPACER_HEIGHT = 30

    DEFAULT_MAP_TOOLS = "pan,wheel_zoom,box_zoom,undo,redo,reset"
    DEFAULT_TOOLS = "pan,wheel_zoom,box_zoom,undo,redo,reset"

    def __init__(self, doc: Document):
        """Initialize an instance."""
        self.doc = doc

        self.column = column()

        self.doc.add_root(self.column)

        self.plots = []
        self.plots.append(
            Plot(
                id="pos_map",
                init=self._generate_pos_map,
                messages={"NAV-PVT": self._update_pos_map},
            )
        )
        self.plots.append(
            Plot(
                id="sv_cno",
                init=self._generate_sv_cno,
                messages={"NAV-SIG": self._update_sv_cno},
            )
        )

    @property
    def required_msgs(self) -> set[str]:
        """Get required messages for all plots."""
        return {msg for plot in self.plots for msg in plot.messages.keys()}

    def get_handlers_for_msg(self, msg_str: str) -> list[Callable]:
        """Get handlers for a message."""
        handlers = []
        for plot in self.plots:
            if msg_str in plot.messages:
                handler = plot.messages[msg_str]
                if handler:
                    handlers.append(handler)

        return handlers

    def get_plot(self, id: str) -> Plot:
        """Get plot by id."""
        for plot in self.plots:
            if plot.id == id:
                return plot

        raise ValueError(f"Plot {id} not found.")

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

    def _set_plot_styles(self, plot: figure) -> None:
        """Set plot styles."""
        # font sizes
        plot.xaxis.axis_label_text_font_size = "14pt"
        plot.yaxis.axis_label_text_font_size = "14pt"
        plot.xaxis.major_label_text_font_size = "12pt"
        plot.yaxis.major_label_text_font_size = "12pt"
        plot.title.text_font_size = "16pt"

        plot.xgrid.grid_line_color = None
        plot.ygrid.grid_line_color = None

        plot.toolbar.autohide = True

    async def _update_pos_map(self, msg: pyubx2.UBXMessage) -> None:
        """Update position on a map."""
        LOGGER.info("Process position map plot")

        plot = self.get_plot("pos_map")

        lat = msg.lat
        lon = msg.lon
        h_acc = msg.hAcc * 1e-3  # convert from mm to meters

        if lat is None or lon is None:
            return

        LOGGER.debug(f"Lat: {lat}, Lon: {lon}")

        x, y = lat_lon_to_web_mercator(lat, lon)
        data = dict(x=[x], y=[y], h_acc=[h_acc])

        if plot.plot is None or plot.datasource is None:
            plot.init(ColumnDataSource(data=data))
        else:
            plot.datasource.patch(
                dict(x=[(slice(None), data["x"])], y=[(slice(None), data["y"])])
            )
            dx = (plot.plot.x_range.end - plot.plot.x_range.start) / 2
            dy = (plot.plot.y_range.end - plot.plot.y_range.start) / 2
            (
                plot.plot.x_range.update(
                    start=plot.datasource.data["x"][0] - dx,
                    end=plot.datasource.data["x"][0] + dx,
                ),
            )
            plot.plot.y_range.update(
                start=plot.datasource.data["y"][0] - dy,
                end=plot.datasource.data["y"][0] + dy,
            )

    async def _update_sv_cno(self, msg: pyubx2.UBXMessage) -> None:
        """Handle SV C/N0 plot."""
        LOGGER.info("Process SV C/N0 plot")

        plot = self.get_plot("sv_cno")

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

        if plot.plot is None or plot.datasource is None:
            plot.init(ColumnDataSource(data=data))
        else:
            plot.datasource.patch(
                dict(
                    y=([(slice(None), data["y"])]),
                    x=([(slice(None), data["x"])]),
                    color=([(slice(None), data["color"])]),
                )
            )
            plot.plot.x_range.factors = self._sort_rinex_sv_ids(
                set(list(plot.plot.x_range.factors) + data["x"])
            )

    def _generate_pos_map(self, datasource: ColumnDataSource) -> None:
        """Plot position on a map."""
        LOGGER.info("Generate position map plot")
        plot = self.get_plot("pos_map")

        p = figure(
            height=self.MAP_PLOT_HEIGHT,
            width=self.DEFAULT_PLOT_WIDTH,
            title="Sijainti",
            x_range=(datasource.data["x"][0] - 100, datasource.data["x"][0] + 100),
            y_range=(datasource.data["y"][0] - 100, datasource.data["y"][0] + 100),
            x_axis_type="mercator",
            y_axis_type="mercator",
            tools=self.DEFAULT_MAP_TOOLS,
        )
        p.add_tile(xyz.OpenStreetMap.Mapnik)
        p.circle(
            x="x",
            y="y",
            radius="h_acc",
            fill_color="blue",
            fill_alpha=0.4,
            source=datasource,
        )
        p.circle(
            x="x", y="y", size=15, fill_color="#d62728", fill_alpha=1, source=datasource
        )

        self._set_plot_styles(p)
        plot.datasource = datasource
        plot.plot = p
        self.column.children.append(Spacer(height=self.SPACER_HEIGHT))
        self.column.children.append(p)

    def _generate_sv_cno(self, datasource: ColumnDataSource) -> None:
        """Generate plot for C/N0 values.

        Plots the C/N0 for the strongest signal for each SV.
        """
        LOGGER.info("Generate SV C/N0 plot")
        plot = self.get_plot("sv_cno")

        p = figure(
            height=self.DEFAULT_PLOT_HEIGHT,
            width=self.DEFAULT_PLOT_WIDTH,
            title="Signaalin voimakkuus",
            tools=self.DEFAULT_TOOLS,
            x_range=self._sort_rinex_sv_ids(datasource.data["x"]),
        )

        p.vbar(x="x", top="y", source=datasource, width=0.9, color="color")

        p.y_range.start = 0
        p.y_range.end = 64
        p.xaxis.major_label_orientation = 3.14 / 4

        p.yaxis.axis_label = "C/N0 [dBHz]"
        p.xaxis.axis_label = "Satelliitti"

        self._set_plot_styles(p)
        plot.datasource = datasource
        plot.plot = p
        self.column.children.append(Spacer(height=self.SPACER_HEIGHT))
        self.column.children.append(p)
