"""Generate plots."""

import gettext
import locale
import logging
import typing
from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path
from threading import Thread

import pyubx2
from bokeh.layouts import Spacer, column, row
from bokeh.models import (  # type: ignore[attr-defined]
    Button,
    Div,
    LayoutDOM,
    MultiChoice,
    Slider,
    Switch,
)
from bokeh.plotting import curdoc

import gnss_visualizer.plots
from gnss_visualizer.plots.generic_plot import GenericContinuousPlot, GenericPlot
from gnss_visualizer.ubx_stream import UbxStreamReader

LOGGER = logging.getLogger(__name__)

locale.setlocale(locale.LC_ALL, "")
lang = gettext.translation(
    "messages", localedir=Path(__file__).parent / "translations", fallback=True
)
lang.install()
_ = lang.gettext


class UIHandler:
    """User interface handler for GNSS Visualizer."""

    TITLE = _("GNSS Visualizer")
    SPACER_HEIGHT = 25

    def __init__(self, input_path: Path, default_simulate_wait_s: float = 0.1):
        """Initialize an instance."""
        self.doc = curdoc()
        self.input = input_path

        self.available_plots: tuple[GenericPlot, ...] = (
            gnss_visualizer.plots.LivePositionMapPlot(),
            gnss_visualizer.plots.LiveSVCnoPlot(),
        )

        self._main_column = column(sizing_mode="stretch_width")
        self._side_column = column()

        self.config = SideLayoutConfiguration(self)
        self.controls = SideLayoutControls(self, default_simulate_wait_s)

        self.doc.add_root(self._get_root_layout())

        self.stream_reader = UbxStreamReader(
            self.input,
            process_msg_callback=self.process_msg,
            get_required_msgs=self.get_required_msgs,
            get_wait_time=self.get_wait_time,
        )
        self._reading_thread: Thread | None = None
        self.read_input()

    @property
    def selected_plots(self) -> list[GenericPlot]:
        """Get selected plots."""
        if self.config.plot_selection is None:
            return []
        return [
            plot
            for plot in self.available_plots
            if plot.name in self.config.plot_selection.value
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

    def get_required_msgs(self) -> set[str]:
        """Get required messages for all selected plots."""
        return {msg for plot in self.selected_plots for msg in plot.required_messages}

    def get_wait_time(self) -> float:
        """Get wait time from user configuration."""
        return typing.cast(float, self.controls.wait_time_slider.value)

    def _get_root_layout(self) -> LayoutDOM:
        """Get the root layout."""
        root_row = row(
            Spacer(width=20),
            self._main_column,
            Spacer(width=40),
            self._side_column,
            Spacer(width=100),
            sizing_mode="stretch_width",
        )
        return column(self.title, root_row, sizing_mode="stretch_width")

    def rewind_file(self) -> None:
        """Rewind the input file."""
        if not self.input.is_file():
            return

        if self._reading_thread is None or not self._reading_thread.is_alive():
            self.read_input()
        else:
            self.stream_reader.rewind_file()

    def read_input(self) -> None:
        """Read input file or device."""
        self._reading_thread = Thread(target=self.stream_reader.read)
        self._reading_thread.start()

    def process_msg(self, msg: pyubx2.UBXMessage, msg_str: str) -> None:
        """Process UBX message.

        Handle read UBX message in a thread-safe way.
        """
        LOGGER.debug(f"Message: {msg_str}")
        for plot in self.get_plots_for_msg(msg_str):
            # run the update in the main thread
            self.doc.add_next_tick_callback(
                partial(self.update_plot, plot=plot, msg=msg)  # type: ignore[arg-type]
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
        self._main_column.children = []  # type: ignore[assignment]
        for plot in plots_to_add:
            self._main_column.children.append(plot.main_layout)  # type: ignore[attr-defined]
            self._main_column.children.append(Spacer(height=self.SPACER_HEIGHT))  # type: ignore[attr-defined]

        self._side_column.children = [self.controls.layout, self.config.layout]  # type: ignore[assignment]

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


class SideLayoutSection(ABC):
    """Base class for side layout sections."""

    def __init__(self) -> None:
        """Initialize an instance."""
        self._layout: LayoutDOM | None = None

    @property
    def layout(self) -> LayoutDOM:
        """Get the layout."""
        if self._layout is None:
            self._layout = self._generate_layout()
        return self._layout

    @abstractmethod
    def _generate_layout(self) -> LayoutDOM:
        """Generate the layout."""

    def _make_side_layout_title_div(self, title: str, level: int = 1) -> Div:
        """Generate a title div for the side layout."""
        if level == 1:
            font_size = "2em"
        elif level == 2:
            font_size = "1.5em"
        else:
            font_size = "1.25em"

        return Div(text=title, styles={"font-size": font_size})


class SideLayoutConfiguration(SideLayoutSection):
    """Configuration for side layout."""

    def __init__(self, ui_handler: UIHandler) -> None:
        """Initialize an instance."""
        super().__init__()

        self.ui_handler = ui_handler

        self.plot_selection = self._generate_plot_selection()

    def _generate_plot_selection(self) -> MultiChoice:
        """Generate plot selection configuration."""
        options = [plot.name for plot in self.ui_handler.available_plots]
        default = [
            plot.name
            for plot in self.ui_handler.available_plots
            if plot.visible_on_start
        ]
        plot_selection = MultiChoice(
            value=default, options=options, sizing_mode="inherit"
        )

        def selection_changed(_attr: str, _old: typing.Any, _new: typing.Any) -> None:
            self.ui_handler.update_layout()

        plot_selection.on_change("value", selection_changed)

        return plot_selection

    def _generate_title_row(self, config_items: LayoutDOM) -> LayoutDOM:
        """Generate title row for the side column."""
        title = self._make_side_layout_title_div(f"{_('Configuration')}", level=1)
        # generate switch to toggle visibility and use it with the title
        visibility_switch = Switch(active=False, align="center")

        def toggle_visibility(_attr: str, _old: bool, new: bool) -> None:
            config_items.visible = new  # type: ignore[assignment]

        visibility_switch.on_change("active", toggle_visibility)
        return row(
            title,
            Spacer(sizing_mode="stretch_width"),
            visibility_switch,
            sizing_mode="stretch_width",
        )

    def _generate_layout(self) -> LayoutDOM:
        """Generate configuration section for the side column."""

        plot_selection_title = self._make_side_layout_title_div(
            _("Select plots"), level=2
        )

        # set all items to column
        config_items = column(
            plot_selection_title,
            self.plot_selection,
            width=400,
            sizing_mode="inherit",
        )
        config_items.visible = False  # type: ignore[assignment]

        title_row = self._generate_title_row(config_items)

        return column(title_row, config_items, sizing_mode="stretch_width")


class SideLayoutControls(SideLayoutSection):
    """Controls for the visualization."""

    def __init__(self, ui_handler: UIHandler, default_simulate_wait_s: float) -> None:
        """Initialize the controls."""
        super().__init__()
        self.ui_handler = ui_handler
        self.rewind_button = Button(
            label=_("Rewind file"), button_type="danger", visible=False
        )
        self.rewind_button.visible = self.ui_handler.input.is_file()

        self.wait_time_slider = Slider(
            start=0,
            end=5,
            value=default_simulate_wait_s,
            step=0.1,
            title=_("Wait between epochs (s)"),
        )
        self.wait_time_slider.visible = self.ui_handler.input.is_file()

    def _generate_layout(self) -> LayoutDOM:
        """Generate controls section for the side column."""
        title = self._make_side_layout_title_div(f"{_('Controls')}", level=1)

        def rewind(_: typing.Any) -> None:
            self.ui_handler.rewind_file()

        self.rewind_button.on_click(rewind)

        control_items = column(
            self.rewind_button,
            self.wait_time_slider,
            width=400,
            sizing_mode="inherit",
        )
        control_items.visible = False  # type: ignore[assignment]
        visibility_switch = Switch(active=False, align="center")
        title_row = row(
            title,
            Spacer(sizing_mode="stretch_width"),
            visibility_switch,
            sizing_mode="stretch_width",
        )

        def toggle_visibility(attr: str, old: bool, new: bool) -> None:
            control_items.visible = new  # type: ignore[assignment]

        visibility_switch.on_change("active", toggle_visibility)
        return column(title_row, control_items, sizing_mode="stretch_width")
