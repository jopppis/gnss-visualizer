"""C/N0 plots for GNSS Visualizer."""

import gettext
import locale
import logging
from math import isnan
from pathlib import Path
from typing import Any

import pyubx2
import xyzservices.providers as xyz
from bokeh.layouts import Spacer, column, row
from bokeh.models import ColumnDataSource, Toggle  # type: ignore[attr-defined]
from bokeh.plotting import figure

from gnss_visualizer.constants import TOP_SPACER_HEIGHT
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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init the instance."""
        super().__init__(*args, **kwargs)
        self._center_map_toggle = self._generate_center_map_toggle()
        self._autozoom_map_toggle = self._generate_autozoom_toggle()

    @property
    def visible_on_start(self) -> bool:
        """Get whether the plot is visible on start."""
        return True

    @property
    def name(self) -> str:
        """Get the name of the plot."""
        return _("Position map (live)")

    @property
    def required_messages(self) -> list[str]:
        """Get required messages for this plot."""
        return ["UBX-NAV-PVT"]

    def _generate_center_map_toggle(self) -> Toggle:
        """Add center map toggle button.

        The button toggles map centering and changes color based on the state of
        the centering.
        """
        toggle = Toggle(
            label=_("Center map"),
            button_type="success",
            active=True,
            sizing_mode="stretch_width",
        )

        def click(_: Any) -> None:
            """Change apperance of the button upon a click."""
            if toggle.active:
                toggle.button_type = "success"
            else:
                toggle.button_type = "default"
                # never autozoom when centering is disabled
                self._autozoom_map_toggle.active = False

        toggle.on_click(click)
        return toggle

    def _generate_autozoom_toggle(self) -> Toggle:
        """Add autozoom toggle button.

        The button toggles map autozoom and changes color based on the state of
        the autozoom.
        """
        toggle = Toggle(
            label=_("Autozoom"),
            button_type="success",
            active=True,
            sizing_mode="stretch_width",
        )

        def click(_: Any) -> None:
            """Change apperance of the button upon a click."""
            if toggle.active:
                toggle.button_type = "success"
                # always center map when autozoom is active
                self._center_map_toggle.active = True
            else:
                toggle.button_type = "default"

        toggle.on_click(click)
        return toggle

    def _update_canvas_extent(self) -> None:
        """Update map canvas extents."""
        if self.datasource is None or self.figure is None:
            return

        if not self._center_map_toggle.active and not self._autozoom_map_toggle.active:
            return

        hacc = self.datasource.data["h_acc"][0]

        if hacc is None:
            return

        # current plot range
        dx_orig = (self.figure.x_range.end - self.figure.x_range.start) / 2  # type: ignore[attr-defined]

        try:
            aspect_ratio = self.figure.inner_height / self.figure.inner_width  # type: ignore[operator]
        except ValueError:
            aspect_ratio = 1

        dx = dx_orig
        if self._autozoom_map_toggle.active:
            # autozoom aka set x scale based on the horizontal accuracy
            if hacc > 10000:
                dx = 10000.0 * 1e3
            elif hacc > 1000:
                dx = 100.0 * 1e3
            elif hacc > 100:
                dx = 10 * 1e3
            elif hacc > 25 or isnan(dx_orig):
                dx = hacc * 5

        dy = dx * aspect_ratio
        self.figure.x_range.update(  # type: ignore[attr-defined]
            start=self.datasource.data["x"][0] - dx,
            end=self.datasource.data["x"][0] + dx,
        )
        self.figure.y_range.update(  # type: ignore[attr-defined]
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
        data: dict[str, Any] = dict(x=[x], y=[y], h_acc=[h_acc], lat=[lat], lon=[lon])
        if self.figure is None or self.datasource is None:
            self.init_plot(ColumnDataSource(data=data))
        else:
            self.datasource.data = data
            self._update_canvas_extent()

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

        self._generate_center_map_toggle()

        side_layout = column(
            Spacer(height=TOP_SPACER_HEIGHT, sizing_mode="fixed"),
            self._center_map_toggle,
            self._autozoom_map_toggle,
            height=self.MAP_PLOT_HEIGHT,
        )

        self.main_layout = row(self.figure, side_layout, sizing_mode="inherit")
