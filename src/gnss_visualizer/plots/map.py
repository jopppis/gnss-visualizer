"""C/N0 plots for GNSS Visualizer."""

import gettext
import locale
import logging
from math import isnan
from pathlib import Path

import pyubx2
import xyzservices.providers as xyz
from bokeh.layouts import Spacer, column
from bokeh.models import ColumnDataSource, Toggle
from bokeh.plotting import figure

from gnss_visualizer.conversions import lat_lon_to_web_mercator
from gnss_visualizer.plots.generic_plot import GenericContinuousPlot
from gnss_visualizer.protocols.ubx import get_full_ubx_msg_id

locale.setlocale(locale.LC_ALL, "")
lang = gettext.translation(
    "messages", localedir=Path(__file__).parent.parent / "translations", fallback=True
)
lang.install()
_ = lang.gettext

LOGGER = logging.getLogger(__name__)


class LivePositionMapPlot(GenericContinuousPlot):
    """Live plot for positions on map."""

    def __init__(self, *args, **kwargs):
        """Init the instance."""
        super().__init__(*args, **kwargs)
        self._center_map_toggle = self._add_center_map_toggle()

    @property
    def required_messages(self) -> list[str]:
        """Get required messages for this plot."""
        return ["UBX-NAV-PVT"]

    def _add_center_map_toggle(self) -> None:
        """Add center map toggle button.

        The button toggles map centering and changes color based on the state of
        the centering.
        """
        toggle = Toggle(
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

        toggle.on_click(center_map_click)
        return toggle

    def _center_map(self) -> None:
        """Center map on the current position."""
        if (
            not self._center_map_toggle.active
            or self.datasource is None
            or self.figure is None
        ):
            return
        hacc = self.datasource.data["h_acc"][0]

        if hacc is None:
            return

        # current plot range
        dx_orig = (self.figure.x_range.end - self.figure.x_range.start) / 2  # type: ignore

        try:
            aspect_ratio = self.figure.inner_height / self.figure.inner_width
        except ValueError:
            aspect_ratio = 1

        # set x scale based on the horizontal accuracy
        if hacc > 10000:
            dx = 10000.0 * 1e3
        elif hacc > 1000:
            dx = 100.0 * 1e3
        elif hacc > 100:
            dx = 10 * 1e3
        elif hacc > 25 or isnan(dx_orig):
            dx = hacc * 5
        else:
            # keep the old range
            dx = dx_orig

        dy = dx * aspect_ratio
        self.figure.x_range.update(
            start=self.datasource.data["x"][0] - dx,
            end=self.datasource.data["x"][0] + dx,
        )
        self.figure.y_range.update(
            start=self.datasource.data["y"][0] - dy,
            end=self.datasource.data["y"][0] + dy,
        )

        LOGGER.debug("Centered map with dx: %s, dy: %s", dx, dy)

    def update_plot(self, msg: pyubx2.UBXMessage) -> None:
        """Update the plot."""
        LOGGER.info("Process position map plot")

        if get_full_ubx_msg_id(msg) != "UBX-NAV-PVT":
            return

        lat = msg.lat
        lon = msg.lon
        h_acc = msg.hAcc * 1e-3  # convert from mm to meters

        if lat is None or lon is None:
            return

        LOGGER.debug(f"Lat: {lat}, Lon: {lon}, hAcc: {h_acc}")

        x, y = lat_lon_to_web_mercator(lat, lon)
        data = dict(x=[x], y=[y], h_acc=[h_acc], lat=[lat], lon=[lon])
        if self.figure is None or self.datasource is None:
            self.init_plot(ColumnDataSource(data=data))
        else:
            self.datasource.data = data
            self._center_map()

    def init_plot(self, datasource: ColumnDataSource) -> None:
        """Initialize the plot."""
        LOGGER.info("Initialize continuous position map plot")

        tooltip = [
            (_("Latitude"), "@{lat}°"),
            (_("Longitude"), "@{lon}°"),
            (_("Horizontal Accuracy"), "@h_acc m"),
        ]

        self.datasource = datasource
        self.figure = figure(
            height=self.MAP_PLOT_HEIGHT,
            title=_("Position map"),
            x_range=(
                self.datasource.data["x"][0] - 1e3,
                self.datasource.data["x"][0] + 1e3,
            ),
            y_range=(
                self.datasource.data["y"][0] - 1e3,
                self.datasource.data["y"][0] + 1e3,
            ),
            x_axis_type="mercator",
            y_axis_type="mercator",
            tools=self.DEFAULT_TOOLS,
            tooltips=tooltip,
            sizing_mode="inherit",
        )
        self.figure.add_tile(xyz.OpenStreetMap.Mapnik)
        self.figure.circle(
            x="x",
            y="y",
            radius="h_acc",
            fill_color="blue",
            fill_alpha=0.4,
            source=self.datasource,
        )
        self.figure.scatter(
            x="x",
            y="y",
            size=15,
            marker="circle",
            fill_color="#d62728",
            fill_alpha=1,
            source=self.datasource,
        )

        self._finalize_figure()

        self._add_center_map_toggle()

        self.side_layout = column(
            Spacer(height=40, sizing_mode="fixed"),
            self._center_map_toggle,
            height=self.MAP_PLOT_HEIGHT,
        )
