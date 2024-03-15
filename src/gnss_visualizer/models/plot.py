"""Data models for plots."""

from collections.abc import Callable
from dataclasses import dataclass

import bokeh.plotting
from bokeh.models import ColumnDataSource, LayoutDOM


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
    layout: LayoutDOM | None = None

    @property
    def layout_item(self) -> LayoutDOM:
        """Get layout item."""
        if self.layout:
            return self.layout
        else:
            return self.figure
