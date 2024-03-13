"""Generate plots."""

import logging
from typing import Callable

import pyubx2
import xyzservices.providers as xyz
from bokeh.document import Document
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.plotting import figure

from gnss_visualizer.constants import UBX_GNSSID_TO_RINEX
from gnss_visualizer.conversions import lat_lon_to_web_mercator
from gnss_visualizer.models.plot import Plot

LOGGER = logging.getLogger(__name__)


class PlotHandler:
    DEFAULT_PLOT_WIDTH = 1200
    DEFAULT_PLOT_HEIGHT = 500
    MAP_PLOT_HEIGHT = 400

    def __init__(self, doc: Document):
        """Initialize an instance."""
        self.doc = doc

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

    async def _update_pos_map(self, msg: pyubx2.UBXMessage) -> None:
        """Update position on a map."""
        LOGGER.info("Updating position on a map")

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

    async def _update_sv_cno(self, msg: pyubx2.UBXMessage) -> None:
        """Handle SV C/N0 plot."""
        LOGGER.info("Updating SV C/N0 plot")

        plot = self.get_plot("sv_cno")

        # make dict of the SV C/N0 values
        cnos: dict[str, int] = {}
        for ix in range(1, msg.numSigs + 1):
            gnss_id = getattr(msg, f"gnssId_{ix:02}")
            sv_id = getattr(msg, f"svId_{ix:02}")
            cno = getattr(msg, f"cno_{ix:02}")

            if cno:
                full_sv_id = f"{UBX_GNSSID_TO_RINEX[gnss_id]}{sv_id}"
                if full_sv_id not in cnos or cno > cnos[full_sv_id]:
                    LOGGER.debug(
                        f"GNSS: {pyubx2.GNSSLIST[gnss_id]}, SV: {sv_id}, C/N0: {cno} dBHz"
                    )
                    cnos[full_sv_id] = cno

        # convert to dict suitable for column data source
        data = dict(x=list(cnos.keys()), y=list(cnos.values()))

        if plot.plot is None or plot.datasource is None:
            plot.init(ColumnDataSource(data=data))
        else:
            plot.datasource.patch(
                dict(
                    y=([(slice(None), data["y"])]),
                    x=([(slice(None), data["x"])]),
                )
            )
            plot.plot.x_range = FactorRange(factors=data["x"])

    def _generate_pos_map(self, datasource: ColumnDataSource) -> None:
        """Plot position on a map."""
        LOGGER.info("Generating SV C/N0 plot")
        plot = self.get_plot("pos_map")

        p = figure(
            height=self.MAP_PLOT_HEIGHT,
            width=self.DEFAULT_PLOT_WIDTH,
            title="Sijainti",
            x_range=(datasource.data["x"][0] - 100, datasource.data["x"][0] + 100),
            y_range=(datasource.data["y"][0] - 100, datasource.data["y"][0] + 100),
            x_axis_type="mercator",
            y_axis_type="mercator",
        )
        p.add_tile(xyz.OpenStreetMap.Mapnik)
        p.circle(
            x="x", y="y", size=10, fill_color="red", fill_alpha=0.8, source=datasource
        )
        p.circle(
            x="x",
            y="y",
            radius="h_acc",
            fill_color="blue",
            fill_alpha=0.4,
            source=datasource,
        )
        plot.datasource = datasource
        plot.plot = p

        self.doc.add_root(p)

    def _generate_sv_cno(self, datasource: ColumnDataSource) -> None:
        """Generate plot for C/N0 values.

        Plots the C/N0 for the strongest signal for each SV.
        """
        LOGGER.info("Generating SV C/N0 plot")
        plot = self.get_plot("sv_cno")

        p = figure(
            height=self.DEFAULT_PLOT_HEIGHT,
            width=self.DEFAULT_PLOT_WIDTH,
            x_range=datasource.data["x"],
            title="Signaalin voimakkuus [dBHz]",
            # toolbar_location=None,
            # tools="",
        )
        # p.x_range = FactorRange(factors=datasource.data["x"])

        plot.datasource = datasource

        p.vbar(x="x", top="y", source=plot.datasource, width=0.9)

        # p.xgrid.grid_line_color = None
        p.y_range.start = 0
        p.y_range.end = 64
        p.xaxis.major_label_orientation = 3.14 / 4

        p.yaxis.axis_label = "C/N0 [dBHz]"
        p.xaxis.axis_label = "Satelliitti"

        # increase font sizes
        p.xaxis.axis_label_text_font_size = "14pt"
        p.yaxis.axis_label_text_font_size = "14pt"
        p.xaxis.major_label_text_font_size = "12pt"
        p.yaxis.major_label_text_font_size = "12pt"
        # increase title font size
        p.title.text_font_size = "16pt"

        plot.plot = p

        self.doc.add_root(p)
