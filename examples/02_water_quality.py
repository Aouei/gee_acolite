"""
Example 2: Water Quality Parameters
Demonstrates computing water quality parameters (SPM, turbidity, chlorophyll)
"""

import ee
import acolite as ac
from gee_acolite import ACOLITE

# Initialize Earth Engine
ee.Initialize()

# Define region of interest (coastal area)
roi = ee.Geometry.Rectangle([-76.5, 38.8, -76.3, 39.0])

# Search for clear image
image = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
    .filterBounds(roi) \
    .filterDate('2023-07-01', '2023-08-31') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
    .first()

print(f"Processing image: {image.get('PRODUCT_ID').getInfo()}")

# Settings with water quality parameters
settings = {
    'aerosol_correction': 'dark_spectrum',
    'dsf_aot_estimate': 'fixed',
    'dsf_model_selection': 'min_drmsd',
    'dsf_spectrum_option': 'darkest',
    'uoz_default': 0.3,
    'uwv_default': 1.5,
    'pressure_default': 1013.25,
    's2_target_res': 10,
    # Enable water quality products
    'l2w_parameters': [
        'spm_nechad2016',      # Suspended particulate matter
        'tur_nechad2016',      # Turbidity
        'chl_oc2',             # Chlorophyll (OC2)
        'chl_oc3',             # Chlorophyll (OC3)
        'ndwi',                # Water index
        'pSDB_green',          # Bathymetry (green)
    ],
    'l2w_mask_threshold': 0.05,
}

# Process image
processor = ACOLITE(ac, settings)
corrected = processor.correct(ee.ImageCollection([image]))
result = corrected.first()

print(f"\nOutput bands: {result.bandNames().getInfo()}")

# Compute statistics for water quality parameters
water_params = ['SPM_Nechad2016_665', 'TUR_Nechad2016_665', 'chl_oc2', 'chl_oc3']

print("\nWater Quality Statistics:")
for param in water_params:
    stats = result.select(param).reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), '', True),
        geometry=roi,
        scale=100,
        bestEffort=True
    ).getInfo()
    
    if f'{param}_mean' in stats and stats[f'{param}_mean'] is not None:
        mean_val = stats[f'{param}_mean']
        std_val = stats.get(f'{param}_stdDev', 0)
        print(f"  {param}: {mean_val:.2f} ± {std_val:.2f}")
    else:
        print(f"  {param}: No data")

print("\n✓ Water quality analysis complete!")
