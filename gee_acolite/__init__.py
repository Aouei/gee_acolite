"""
GEE ACOLITE - Atmospheric correction for Google Earth Engine

This package provides ACOLITE atmospheric correction optimized for 
Google Earth Engine workflows with Sentinel-2 imagery.

Main Features:
- Dark spectrum fitting atmospheric correction
- AOT estimation (fixed geometry)
- Water quality parameter computation
- Cloud masking integration

Note: Requires ACOLITE package to be installed separately.
Install from: https://github.com/acolite/acolite

Usage
-----
Import specific components directly from their modules:

    from gee_acolite.correction import ACOLITE
    from gee_acolite.bathymetry import multi_image
    from gee_acolite.water_quality import compute_water_bands, compute_water_mask, PRODUCTS
"""

try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    __version__ = _pkg_version("gee_acolite")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "unknown"

__author__ = "Sergio"
__license__ = "GPL-3.0"

__all__ = [
    # Main class
    "ACOLITE",
    # Bathymetry
    "multi_image",
    # Water quality
    "compute_water_bands",
    "compute_water_mask",
    "PRODUCTS",
]
