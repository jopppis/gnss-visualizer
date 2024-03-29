"""Generic plot handling for GNSS Visualizer."""

from abc import ABC, abstractmethod

import pyubx2
from bokeh.models import ColumnDataSource, LayoutDOM
from bokeh.plotting import figure


class GenericPlot(ABC):
    """Plot creation for all plots in GNSS Visualizer."""

    DEFAULT_PLOT_HEIGHT = 400
    MAP_PLOT_HEIGHT = 380

    DEFAULT_TOOLS = "pan,wheel_zoom,zoom_out,box_zoom,hover,undo,redo,reset"

    def __init__(self) -> None:
        """Initialize an instance."""
        self._name: str | None = None

        self.figure: figure | None = None
        self.datasource: ColumnDataSource | None = None

        self._main_layout: LayoutDOM | None = None

        self.initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the plot."""

    @property
    @abstractmethod
    def required_messages(self) -> list[str]:
        """Get required messages for this plot."""

    @property
    @abstractmethod
    def continuous(self) -> bool:
        """Get whether the plot is continuous.

        Continuous plots show data for and epoch (with possible history) and
        update when new data arrives whereas non-continuous plots show data for
        the full file at once and do not update after creation.
        """

    @property
    def visible_on_start(self) -> bool:
        """Get whether the plot is visible on start."""
        return False

    @property
    def main_layout(self) -> LayoutDOM | None:
        """Get layout item for this plot.

        This can be just the figure for the plot or some layout encompassing the
        figure and something else.
        """
        if self._main_layout:
            return self._main_layout
        else:
            return self.figure

    @main_layout.setter
    def main_layout(self, layout: LayoutDOM) -> None:
        """Set the main layout to be used for the plot.

        This can be used to append other models besides just the figure.
        """
        self._main_layout = layout

    def _finalize_figure(self) -> None:
        """Set plot styles."""
        if self.figure is None:
            return

        # font sizes
        self.figure.xaxis.axis_label_text_font_size = "14pt"
        self.figure.yaxis.axis_label_text_font_size = "14pt"
        self.figure.xaxis.major_label_text_font_size = "12pt"
        self.figure.yaxis.major_label_text_font_size = "12pt"
        self.figure.title.text_font_size = "16pt"

        self.figure.xgrid.grid_line_color = None
        self.figure.ygrid.grid_line_color = None

        self.figure.toolbar.autohide = True

        # mark the plot as initialized
        self.initialized = True


class GenericNonContinousPlot(GenericPlot):
    """Generic class for all plots that present non-continuous data.

    Non-continuous plots show data for full file at once and not updated after
    creation.
    """

    @property
    def continuous(self) -> bool:
        """Get whether the plot is continuous.

        Continuous plots show data for and epoch (with possible history) and
        update when new data arrives.
        """
        return True

    @abstractmethod
    def generate_plot(self) -> None:
        """Generate the plot."""


class GenericContinuousPlot(GenericPlot):
    """Generic class for all plots that present continuous data."""

    @property
    def continuous(self) -> bool:
        """Get whether the plot is continuous.

        Continuous plots show data for and epoch (with possible history) and
        update when new data arrives.
        """
        return True

    @abstractmethod
    def update_plot(self, msg: pyubx2.UBXMessage) -> None:
        """Update the plot when new data arrives."""
        pass

    @abstractmethod
    def init_plot(self, datasource: ColumnDataSource) -> None:
        """Initialize the plot."""
