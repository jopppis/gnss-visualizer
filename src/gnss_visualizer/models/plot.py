"""Data models for plots."""

from collections.abc import Callable
from dataclasses import dataclass

from bokeh.models import Column, ColumnDataSource
from bokeh.plotting import figure


@dataclass
class Plot:
    """Model for a plot."""

    id: str
    init: Callable
    messages: dict[str, Callable | None]
    priority: int = -1
    visible: bool = False
    datasource: ColumnDataSource | None = None
    plot: figure | None = None
    column: Column | None = None

    @property
    def layout_item(self) -> Column | figure:
        """Get layout item."""
        if self.column:
            return self.column
        else:
            return self.plot
