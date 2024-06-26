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
def ui_handler(nav_pvt_message_file: Path) -> UIHandler:
    """Fixture to create a UIHandler instance with mocked dependencies."""
    handler = UIHandler(nav_pvt_message_file)
    return handler


def test_initialization(
    mock_ubx_stream_reader: MagicMock, nav_pvt_message_file: Path
) -> None:
    """Test that the UIHandler is correctly initialized."""
    with patch(
        "gnss_visualizer.ui_handler.UbxStreamReader",
        return_value=mock_ubx_stream_reader,
    ):
        handler = UIHandler(nav_pvt_message_file)

        assert handler.input == nav_pvt_message_file
        assert isinstance(handler.doc, Document)
        handler.stream_reader.read.assert_called_once()  # type: ignore[attr-defined]


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
    """Test that the file reading is triggered when requested."""
    with patch("gnss_visualizer.ubx_stream.UbxStreamReader.read") as read_mock:
        ui_handler.read_input()
        read_mock.assert_called_once()


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


def test_rewind_file(ui_handler: UIHandler) -> None:
    """Test the rewind_file method."""
    with patch(
        "gnss_visualizer.ui_handler.UbxStreamReader.rewind_file",
    ):
        ui_handler.rewind_file()
        ui_handler.stream_reader.rewind_file.assert_called_once()


def test_update_layout_no_plots(ui_handler: UIHandler):
    """Test the update_layout method."""
    ui_handler.update_layout()
    assert len(ui_handler._main_column.children) == 0
    assert len(ui_handler._side_column.children) == 2
