import unittest
from pathlib import Path

from bokeh.plotting import curdoc
from gnss_visualizer.ubx_stream import UbxStreamReader
from gnss_visualizer.ui_handler import UIHandler


class TestFileReading(unittest.TestCase):
    def setUp(self) -> None:
        self.file = Path(__file__).parent / "coldstart.ubx"
        self.ui_handler = UIHandler(curdoc(), True, 0.1)
        self.simulate_wait_s = 1.0
        self.ubx_stream = UbxStreamReader(self.file, self.ui_handler)

    def test_init(self) -> None:
        self.assertEqual(self.ubx_stream.file, self.file)
        self.assertEqual(self.ubx_stream.ui_handler, self.ui_handler)


if __name__ == "__main__":
    unittest.main()
