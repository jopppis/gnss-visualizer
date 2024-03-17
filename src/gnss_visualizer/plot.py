"""Generate plots."""

import gettext
import locale
import logging
from math import isnan
from pathlib import Path
from typing import Any, Callable, Iterable

import pyubx2
import xyzservices.providers as xyz
from bokeh.document import Document
from bokeh.layouts import Spacer, column, row
from bokeh.models import ColumnDataSource, Div, Toggle
from bokeh.plotting import figure

from gnss_visualizer.constants import RINEX_CONSTELLATION_COLORS, UBX_GNSSID_TO_RINEX
from gnss_visualizer.conversions import lat_lon_to_web_mercator
from gnss_visualizer.models.plot import Plot

LOGGER = logging.getLogger(__name__)

locale.setlocale(locale.LC_ALL, "")
lang = gettext.translation(
    "messages", localedir=Path(__file__).parent / "translations", fallback=True
)
lang.install()
_ = lang.gettext


class PlotHandler:
    """Generate plots from GNSS receiver messages."""

    DEFAULT_PLOT_HEIGHT = 400
    MAP_PLOT_HEIGHT = 380
    SPACER_HEIGHT = 25

    DEFAULT_MAP_TOOLS = "pan,wheel_zoom,zoom_out,box_zoom,hover,undo,redo,reset"
    DEFAULT_TOOLS = "pan,wheel_zoom,zoom_out,box_zoom,hover,undo,redo,reset"

    TITLE = _("GNSS Visualizer")

    def __init__(self, doc: Document):
        """Initialize an instance."""
        self.doc = doc

        self._main_column = column(sizing_mode="stretch_width")
        self._side_column = column()

        title_div = Div(
            text=f"<h1>{self.TITLE}</h1>",
            styles={
                "text-align": "center",
            },
            height=20,
            sizing_mode="stretch_width",
        )

        root_row = row(
            self._main_column,
            self._side_column,
            Spacer(width=100),
            sizing_mode="stretch_width",
        )
        root_column = column(title_div, root_row, sizing_mode="stretch_width")

        self.doc.add_root(root_column)

        self.plots = []
        self.plots.append(
            Plot(
                id="pos_map",
                init=self._generate_pos_map,
                messages={"NAV-PVT": self._update_pos_map},
                priority=1,
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

    def _center_map(self, plot: Plot) -> None:
        """Center map on the current position."""
        if (
            not self._center_map_toggle.active
            or plot.datasource is None
            or plot.figure is None
        ):
            return
        hacc = plot.datasource.data["h_acc"][0]

        if hacc is None:
            return

        # current plot range
        dx_orig = (plot.figure.x_range.end - plot.figure.x_range.start) / 2

        aspect_ratio = plot.figure.inner_height / plot.figure.inner_width

        # set x scale based on the horizontal accuracy
        if hacc > 10000:
            dx = 10000.0 * 1e3
        elif hacc > 1000:
            dx = 100.0 * 1e3
        elif hacc > 100:
            dx = 10 * 1e3
        elif hacc > 50 or isnan(dx_orig):
            dx = 1e3
        else:
            # keep the old range
            dx = dx_orig

        dy = dx * aspect_ratio
        plot.figure.x_range.update(
            start=plot.datasource.data["x"][0] - dx,
            end=plot.datasource.data["x"][0] + dx,
        )
        plot.figure.y_range.update(
            start=plot.datasource.data["y"][0] - dy,
            end=plot.datasource.data["y"][0] + dy,
        )

        LOGGER.debug("Centered map with dx: %s, dy: %s", dx, dy)

    async def _update_pos_map(self, msg: pyubx2.UBXMessage) -> None:
        """Update position on a map."""
        LOGGER.info("Process position map plot")

        plot = self.get_plot("pos_map")

        lat = msg.lat
        lon = msg.lon
        h_acc = msg.hAcc * 1e-3  # convert from mm to meters

        if lat is None or lon is None:
            return

        LOGGER.debug(f"Lat: {lat}, Lon: {lon}, hAcc: {h_acc}")

        x, y = lat_lon_to_web_mercator(lat, lon)
        data = dict(x=[x], y=[y], h_acc=[h_acc], lat=[lat], lon=[lon])
        if plot.figure is None or plot.datasource is None:
            plot.init(ColumnDataSource(data=data))
        else:
            plot.datasource.data = data
            self._center_map(plot)

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

        if plot.figure is None or plot.datasource is None:
            plot.init(ColumnDataSource(data=data))
        else:
            plot.datasource.data = data
            plot.figure.x_range.factors = self._sort_rinex_sv_ids(
                set(list(plot.figure.x_range.factors) + data["x"])
            )

    def _add_plot_to_column(self, plot: Plot) -> None:
        """Add plot to column.

        Regenerate entire column by adding all plots to the column.

        Also set the new plot as visible.

        Set the column order based on priority. Higher priority values go
        before lower values.
        """
        if plot.figure is None or plot.visible:
            return

        plot.visible = True

        plots_to_add = [
            plot for plot in self.plots if plot.visible and plot.figure is not None
        ]
        plots_prioritized = sorted(plots_to_add, key=lambda x: x.priority, reverse=True)

        for plot in plots_prioritized:
            self._main_column.children.append(plot.main_layout)
            self._main_column.children.append(Spacer(height=self.SPACER_HEIGHT))
            self._side_column.children.append(plot.side_layout)
            self._side_column.children.append(Spacer(height=self.SPACER_HEIGHT))

    def _generate_pos_map(self, datasource: ColumnDataSource) -> None:
        """Plot position on a map."""
        LOGGER.info("Generate position map plot")
        plot = self.get_plot("pos_map")

        tooltip = [
            ("Leveysaste", "@{lat}°"),
            ("Pituusaste", "@{lon}°"),
            ("Tarkkuus", "@h_acc m"),
        ]

        p = figure(
            height=self.MAP_PLOT_HEIGHT,
            title=_("Position map"),
            x_range=(datasource.data["x"][0] - 1e3, datasource.data["x"][0] + 1e3),
            y_range=(datasource.data["y"][0] - 1e3, datasource.data["y"][0] + 1e3),
            x_axis_type="mercator",
            y_axis_type="mercator",
            tools=self.DEFAULT_MAP_TOOLS,
            tooltips=tooltip,
            sizing_mode="inherit",
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

        # create button that toggles map_centering and changes color based on the state of the centering
        self._center_map_toggle = Toggle(
            label=_("Center map"),
            button_type="success",
            active=True,
        )

        def center_map_click(_) -> None:
            """Change apperance of center map button upon a click."""
            if self._center_map_toggle.active:
                self._center_map_toggle.button_type = "success"
            else:
                self._center_map_toggle.button_type = "default"

        self._center_map_toggle.on_click(center_map_click)

        self._set_plot_styles(p)
        plot.datasource = datasource
        plot.figure = p
        plot.side_layout = column(
            Spacer(height=40, sizing_mode="fixed"),
            self._center_map_toggle,
            height=self.MAP_PLOT_HEIGHT,
        )
        self._add_plot_to_column(plot)

    def _generate_sv_cno(self, datasource: ColumnDataSource) -> None:
        """Generate plot for C/N0 values.

        Plots the C/N0 for the strongest signal for each SV.
        """
        LOGGER.info("Generate SV C/N0 plot")
        plot = self.get_plot("sv_cno")

        y_label = "C/N0 [dBHz]"
        x_label = _("Satellite")

        tooltip = [
            (x_label, "@x"),
            (y_label, "@y"),
        ]

        p = figure(
            height=self.DEFAULT_PLOT_HEIGHT,
            title=_("Signal strength"),
            tools=self.DEFAULT_TOOLS,
            tooltips=tooltip,
            x_range=self._sort_rinex_sv_ids(datasource.data["x"]),
            sizing_mode="inherit",
        )

        p.vbar(x="x", top="y", source=datasource, width=0.9, color="color")

        p.y_range.start = 0
        p.y_range.end = 64
        p.xaxis.major_label_orientation = 3.14 / 4

        p.yaxis.axis_label = y_label
        p.xaxis.axis_label = x_label

        self._set_plot_styles(p)
        plot.datasource = datasource
        plot.figure = p
        self._add_plot_to_column(plot)
