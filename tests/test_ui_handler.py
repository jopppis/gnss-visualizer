"""Unit tests for ui_handler.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from bokeh.document import Document
from gnss_visualizer.ubx_stream import UbxStreamReader
from gnss_visualizer.ui_handler import UIHandler


@pytest.fixture
def mock_ubx_stream_reader() -> MagicMock:
    """Fixture to create a mock UbxStreamReader."""
    return MagicMock(spec=UbxStreamReader)


@pytest.fixture
def ui_handler(mock_ubx_stream_reader: UbxStreamReader) -> UIHandler:
    """Fixture to create a UIHandler instance with mocked dependencies."""
    with patch(
        "gnss_visualizer.ui_handler.UbxStreamReader",
        return_value=mock_ubx_stream_reader,
    ):
        handler = UIHandler(Path("input_path"))
    return handler


def test_initialization(ui_handler: UIHandler) -> None:
    """Test that the UIHandler is correctly initialized."""
    assert ui_handler.input == Path("input_path")
    assert isinstance(ui_handler.doc, Document)
    ui_handler.stream_reader.read.assert_called_once()  # type: ignore[attr-defined]


def test_initial_selected_plots(ui_handler: UIHandler) -> None:
    """Test the initial state of selected_plots property."""
    selected_plots = ui_handler.selected_plots
    assert len(selected_plots) == 1
    assert selected_plots[0].name == "Position map (live)"


def test_initial_get_required_msgs(ui_handler: UIHandler) -> None:
    """Test the get_required_msgs method."""
    required_msgs = ui_handler.get_required_msgs()
    assert required_msgs == {"UBX-NAV-PVT"}


def test_get_wait_time(ui_handler: UIHandler) -> None:
    """Test the get_wait_time method."""
    ui_handler.controls.wait_time_slider = MagicMock(value=0.5)
    wait_time = ui_handler.get_wait_time()
    assert wait_time == 0.5


def test_read_input(
    ui_handler: UIHandler, mock_ubx_stream_reader: UbxStreamReader
) -> None:
    """Test that the file is initially read."""
    mock_ubx_stream_reader.read.assert_called_once()  # type: ignore[attr-defined]


def test_process_msg(ui_handler: UIHandler) -> None:
    """Test the process_msg method."""
    with patch(
        "bokeh.document.Document.add_next_tick_callback"
    ) as mock_add_next_tick_callback, patch(
        "gnss_visualizer.ui_handler.UIHandler.get_plots_for_msg",
        return_value=[MagicMock()],
    ):
        msg_mock = MagicMock()

        # Execute the function that is expected to use the mocked methods
        ui_handler.process_msg(msg_mock, "msg_str")

        # Assert that add_next_tick_callback was called once
        mock_add_next_tick_callback.assert_called_once()


# def test_update_layout(ui_handler: UIHandler):
#     """Test the update_layout method."""
#     ui_handler.update_layout()
#     assert len(ui_handler._main_column.children) > 0
#     assert len(ui_handler._side_column.children) > 0


# def test_update_plot(ui_handler: UIHandler):
#     """Test the update_plot method."""
#     plot_mock = MagicMock(initialized=False)
#     msg_mock = MagicMock()
#     ui_handler.update_plot(plot_mock, msg_mock)
#     plot_mock.update_plot.assert_called_once_with(msg_mock)
#     ui_handler.update_layout.assert_called_once()


# def test_get_plots_for_msg(ui_handler: UIHandler):
#     """Test the get_plots_for_msg method."""
#     plot_mock = MagicMock(can_handle_msg=MagicMock(return_value=True))
#     ui_handler.available_plots = [plot_mock]
#     plots = ui_handler.get_plots_for_msg("msg_str")
#     assert len(plots) == 1
#     assert plots[0] == plot_mock
