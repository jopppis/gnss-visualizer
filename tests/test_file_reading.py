import unittest
from pathlib import Path

from bokeh.plotting import curdoc
from gnss_visualizer.plot import PlotHandler
from gnss_visualizer.ubx_stream import UbxStreamReader


class TestFileReading(unittest.TestCase):
    def setUp(self):
        self.file = Path(__file__).parent / "coldstart.ubx"
        self.plot_handler = PlotHandler(curdoc())
        self.simulate_wait_s = 1.0
        self.ubx_stream = UbxStreamReader(
            self.file, self.plot_handler, self.simulate_wait_s
        )

    def test_init(self):
        self.assertEqual(self.ubx_stream.file, self.file)
        self.assertEqual(self.ubx_stream.plot_handler, self.plot_handler)
        self.assertEqual(self.ubx_stream.simulate_wait_s, self.simulate_wait_s)


if __name__ == "__main__":
    unittest.main()
