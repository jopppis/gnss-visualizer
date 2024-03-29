"""Generate plots."""

import gettext
import locale
import logging
from pathlib import Path

import pyubx2
from bokeh.document import Document
from bokeh.layouts import Spacer, column, row
from bokeh.models import Div, LayoutDOM, MultiChoice

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

        self._main_column = column(sizing_mode="stretch_width")
        self._side_column = column()

        self._plot_selection: MultiChoice | None = None
        self._config = self._generate_configuration()

        root_row = row(
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

        self._side_column.children = [self._config]

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

    def _generate_configuration(self) -> LayoutDOM:
        """Add configuration section to the side column."""
        title = Div(text=f"{_('Configuration')}", styles={"font-size": "2em"})
        plot_selection_title = Div(
            text=_("Select plots"), styles={"font-size": "1.5em"}
        )
        options = [plot.name for plot in self.available_plots]
        default = [plot.name for plot in self.available_plots if plot.visible_on_start]
        self._plot_selection = MultiChoice(
            value=default, options=options, sizing_mode="inherit"
        )

        def selection_changed(attr, old, new):
            self.update_layout()

        self._plot_selection.on_change("value", selection_changed)
        return column(
            title,
            plot_selection_title,
            self._plot_selection,
            width=400,
            sizing_mode="inherit",
        )
