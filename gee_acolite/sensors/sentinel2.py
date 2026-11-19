"""
Sentinel-2 sensor configuration and band definitions.

This module defines constants for Sentinel-2 MSI bands and their native spatial resolutions.
"""

# List of all Sentinel-2 MSI bands
SENTINEL2_BANDS = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']

# Nominal central wavelength (nm) of each band (Sentinel-2A, rounded). ACOLITE selects the bands used by
# ``l2w_mask_negative_wave_range`` by wavelength; S2B differs by a few nm, which does not change the selection.
BAND_WAVELENGTHS = {
    'B1': 443, 'B2': 492, 'B3': 560, 'B4': 665, 'B5': 704, 'B6': 740, 'B7': 783,
    'B8': 833, 'B8A': 865, 'B9': 945, 'B10': 1373, 'B11': 1614, 'B12': 2202,
}

# Mapping of target spatial resolution (in meters) to representative band
# Used for resampling operations to ensure consistent projection
BAND_BY_SCALE = {
    10: 'B2',   # 10m: Blue band (490nm) - used for 10m resolution products
    20: 'B5',   # 20m: Red Edge 1 (705nm) - used for 20m resolution products
    60: 'B1',   # 60m: Coastal Aerosol (443nm) - used for 60m resolution products
}