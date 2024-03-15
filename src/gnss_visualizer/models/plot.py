"""Data models for plots."""

from collections.abc import Callable
from dataclasses import dataclass

import bokeh.plotting
from bokeh.models import ColumnDataSource, LayoutDOM, Spacer


@dataclass
class Plot:
    """Model for a plot."""

    id: str
    init: Callable
    messages: dict[str, Callable | None]
    priority: int = -1
    visible: bool = False
    datasource: ColumnDataSource | None = None
    figure: bokeh.plotting.figure | None = None

    _main_layout: LayoutDOM | None = None
    _side_layout: LayoutDOM | None = None

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

    @property
    def side_layout(self) -> LayoutDOM | None:
        """Get side layout item for this plot.

        Side layout can be used to show extra information or controls besides a
        plot.
        """
        if self._side_layout:
            return self._side_layout
        else:
            if self.main_layout is None:
                return None
            return Spacer(height=self.main_layout.height)

    @side_layout.setter
    def side_layout(self, layout: LayoutDOM) -> None:
        """Set the side layout to be used for the plot."""
        self._side_layout = layout
