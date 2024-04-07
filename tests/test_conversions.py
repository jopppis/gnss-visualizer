"""Unit tests for conversions.py"""

import numpy as np
from gnss_visualizer.conversions import lat_lon_to_web_mercator


def test_lat_lon_to_webmercator() -> None:
    """Test conversion from lat/lon to Web Mercator"""
    lat = 50
    lon = -50
    num_digits = 6
    expected_x = round(-5565974.539663672, num_digits)
    expected_y = round(6446275.841017148, num_digits)

    x, y = lat_lon_to_web_mercator(lat, lon)

    assert round(x, num_digits) == expected_x
    assert round(y, num_digits) == expected_y


def test_lat_lon_to_webmercator_invalid() -> None:
    """Test conversion from lat/lon to Web Mercator with invalid input."""
    lat = 91
    lon = 181
    expected_x = np.inf
    expected_y = np.inf

    x, y = lat_lon_to_web_mercator(lat, lon)

    assert x == expected_x
    assert y == expected_y
