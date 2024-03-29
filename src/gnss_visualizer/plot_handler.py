"""Generate plots."""

import gettext
import locale
import logging
from pathlib import Path
from typing import Any

import pyubx2
from bokeh.document import Document
from bokeh.layouts import Spacer, column, row
from bokeh.models import Button, Div, LayoutDOM, MultiChoice, Switch

import gnss_visualizer.plots
from gnss_visualizer.plots.generic_plot import GenericContinuousPlot, GenericPlot

LOGGER = logging.getLogger(__name__)

locale.setlocale(locale.LC_ALL, "")
lang = gettext.translation(
    "messages", localedir=Path(__file__).parent / "translations", fallback=True
)
lang.install()
_ = lang.gettext


class PlotHandler:
    """Generate plots from GNSS receiver messages."""

    TITLE = _("GNSS Visualizer")
    SPACER_HEIGHT = 25

    def __init__(self, doc: Document):
        """Initialize an instance."""
        self.doc = doc

        self.available_plots: tuple[GenericPlot, ...] = (
            gnss_visualizer.plots.LivePositionMapPlot(),
            gnss_visualizer.plots.LiveSVCnoPlot(),
        )

        # flag for rewinding the stream
        self.request_file_rewind = False
        self.rewind_button = Button(
            label=_("Rewind file"), button_type="danger", visible=False
        )

        self._main_column = column(sizing_mode="stretch_width")
        self._side_column = column()

        self._plot_selection: MultiChoice | None = None
        self._config = self._generate_configuration()
        self._controls = self._generate_controls()

        root_row = row(
            Spacer(width=20),
            self._main_column,
            Spacer(width=40),
            self._side_column,
            Spacer(width=100),
            sizing_mode="stretch_width",
        )
        root_column = column(self.title, root_row, sizing_mode="stretch_width")

        self.doc.add_root(root_column)

    @property
    def required_msgs(self) -> set[str]:
        """Get required messages for all selected plots."""
        return {msg for plot in self.selected_plots for msg in plot.required_messages}

    @property
    def selected_plots(self) -> list[GenericPlot]:
        """Get selected plots."""
        if self._plot_selection is None:
            return []
        return [
            plot
            for plot in self.available_plots
            if plot.name in self._plot_selection.value
        ]

    @property
    def title(self) -> Div:
        """Get title for the page."""
        return Div(
            text=f"<h1>{self.TITLE}</h1>",
            styles={
                "text-align": "center",
            },
            height=40,
            sizing_mode="stretch_width",
        )

    def update_layout(self) -> None:
        """Add plot to column.

        Regenerate entire column by adding all plots to the column.
        """
        plots_to_add = [
            plot
            for plot in self.selected_plots
            if plot.initialized and plot.figure is not None
        ]
        self._main_column.children = []
        for plot in plots_to_add:
            self._main_column.children.append(plot.main_layout)
            self._main_column.children.append(Spacer(height=self.SPACER_HEIGHT))

        self._side_column.children = [self._controls, self._config]

    async def update_plot(
        self, plot: GenericContinuousPlot, msg: pyubx2.UBXMessage
    ) -> None:
        """Request an update of a plot."""
        init_before = plot.initialized
        plot.update_plot(msg)

        if not init_before and plot.initialized:
            self.update_layout()

    def get_plots_for_msg(self, msg_str: str) -> list[GenericContinuousPlot]:
        """Get handlers for a message."""
        plots = []
        for plot in self.selected_plots:
            if not isinstance(plot, GenericContinuousPlot):
                continue
            if msg_str in plot.required_messages:
                plots.append(plot)

        return plots

    def _make_side_layout_title_div(self, title: str, level: int = 1) -> Div:
        """Generate a title div for the side layout."""
        if level == 1:
            font_size = "2em"
        elif level == 2:
            font_size = "1.5em"
        else:
            font_size = "1.25em"

        return Div(text=title, styles={"font-size": font_size})

    def _generate_plot_selection_config(self):
        """Generate plot selection configuration."""
        options = [plot.name for plot in self.available_plots]
        default = [plot.name for plot in self.available_plots if plot.visible_on_start]
        self._plot_selection = MultiChoice(
            value=default, options=options, sizing_mode="inherit"
        )

        def selection_changed(attr: str, old: Any, new: Any):
            self.update_layout()

        self._plot_selection.on_change("value", selection_changed)

    def _generate_configuration(self) -> LayoutDOM:
        """Generate configuration section for the side column."""
        title = self._make_side_layout_title_div(f"{_('Configuration')}", level=1)

        self._generate_plot_selection_config()
        plot_selection_title = self._make_side_layout_title_div(
            _("Select plots"), level=2
        )

        # set all items to column
        config_items = column(
            plot_selection_title,
            self._plot_selection,
            width=400,
            sizing_mode="inherit",
        )
        config_items.visible = False

        # generate switch to toggle visibility and use it with the title
        visibility_switch = Switch(active=False, align="center")

        def toggle_visibility(attr: str, old: bool, new: bool):
            config_items.visible = new

        visibility_switch.on_change("active", toggle_visibility)
        title_row = row(
            title,
            Spacer(sizing_mode="stretch_width"),
            visibility_switch,
            sizing_mode="stretch_width",
        )

        return column(title_row, config_items, sizing_mode="stretch_width")

    def _generate_controls(self) -> LayoutDOM:
        """Generate controls section for the side column."""
        title = self._make_side_layout_title_div(f"{_('Controls')}", level=1)

        def request_rewind(_: Any) -> None:
            self.request_file_rewind = True

        self.rewind_button.on_click(request_rewind)
        control_items = column(
            self.rewind_button,
            width=400,
            sizing_mode="inherit",
        )
        control_items.visible = False
        visibility_switch = Switch(active=False, align="center")
        title_row = row(
            title,
            Spacer(sizing_mode="stretch_width"),
            visibility_switch,
            sizing_mode="stretch_width",
        )

        def toggle_visibility(attr: str, old: bool, new: bool):
            control_items.visible = new

        visibility_switch.on_change("active", toggle_visibility)
        return column(title_row, control_items, sizing_mode="stretch_width")
