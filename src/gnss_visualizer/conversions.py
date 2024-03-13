"""Conversions between units and measures."""

import pyproj


def lat_lon_to_web_mercator(lat: float, lon: float) -> tuple[float, float]:
    """Convert latitude and longitude to Web Mercator."""
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857")
    x, y = transformer.transform(lat, lon)
    return x, y
