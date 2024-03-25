from .cno import LiveSVCnoPlot
from .map import LivePositionMapPlot

__all__ = ["LivePositionMapPlot", "LiveSVCnoPlot"]

PLOTS = [LivePositionMapPlot, LiveSVCnoPlot]
