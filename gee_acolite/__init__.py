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
"""

__version__ = "0.1.0"
__author__ = "Sergio"
__license__ = "GPL-3.0"

# Main atmospheric correction class
from gee_acolite.correction import ACOLITE

# Bathymetry utilities
from gee_acolite.bathymetry import multi_image

# Water quality parameters
from gee_acolite.water_quality import (
    compute_water_bands,
    compute_water_mask,
    PRODUCTS
)

# Utility modules
from gee_acolite import utils, sensors

__all__ = [
    # Main class
    "ACOLITE",
    # Bathymetry
    "multi_image",
    # Water quality
    "compute_water_bands",
    "compute_water_mask",
    "PRODUCTS",
    # Modules
    "utils",
    "sensors",
]
