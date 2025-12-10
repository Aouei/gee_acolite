"""
Example 1: Basic Usage of GEE ACOLITE
Demonstrates simple atmospheric correction workflow
"""

import ee
import acolite as ac
from gee_acolite import ACOLITE

# Initialize Earth Engine
ee.Initialize()

# Define region of interest (Chesapeake Bay)
roi = ee.Geometry.Point([-76.7, 38.2])

# Search for Sentinel-2 images
images = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
    .filterBounds(roi) \
    .filterDate('2023-06-01', '2023-06-30') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
    .limit(5)

print(f"Found {images.size().getInfo()} images")

# Configure basic settings
settings = {
    'aerosol_correction': 'dark_spectrum',
    'dsf_aot_estimate': 'fixed',
    'dsf_model_selection': 'min_drmsd',
    'dsf_spectrum_option': 'darkest',
    'dsf_nbands': 2,
    'uoz_default': 0.3,
    'uwv_default': 1.5,
    'pressure_default': 1013.25,
    'wind_default': 2.0,
    's2_target_res': 10,
}

# Apply atmospheric correction
processor = ACOLITE(ac, settings)
corrected_images, final_settings = processor.correct(images)

print(f"\nProcessed {corrected_images.size().getInfo()} images successfully!")
print(f"Output bands: {corrected_images.first().bandNames().getInfo()[:5]}...")

# Get info about first corrected image
first_image = corrected_images.first()
image_date = ee.Date(first_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
print(f"\nFirst image date: {image_date}")

# Sample a point to see reflectance values
sample_point = roi
sample_data = first_image.select(['rhos_B2', 'rhos_B3', 'rhos_B4']).sample(
    region=sample_point,
    scale=10,
    numPixels=1
).first().getInfo()

print(f"\nSample reflectance values:")
for band, value in sample_data['properties'].items():
    print(f"  {band}: {value:.4f}")
