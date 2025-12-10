"""
Example 3: Batch Processing
Process multiple images and compute time series statistics
"""

import ee
import acolite as ac
from gee_acolite import ACOLITE

# Initialize Earth Engine
ee.Initialize()

# Define study area
roi = ee.Geometry.Point([-76.7, 38.2]).buffer(5000)

# Search for images over summer season
start_date = '2023-06-01'
end_date = '2023-09-30'

images = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
    .filterBounds(roi) \
    .filterDate(start_date, end_date) \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))

n_images = images.size().getInfo()
print(f"Found {n_images} images between {start_date} and {end_date}")

# Settings for batch processing
settings = {
    'aerosol_correction': 'dark_spectrum',
    'dsf_aot_estimate': 'fixed',
    'dsf_model_selection': 'min_drmsd',
    'dsf_spectrum_option': 'darkest',
    'dsf_nbands': 2,
    'uoz_default': 0.3,
    'uwv_default': 1.5,
    'pressure_default': 1013.25,
    's2_target_res': 10,
    'l2w_parameters': ['spm_nechad2016'],
}

# Process all images
print("\nProcessing images...")
processor = ACOLITE(ac, settings)
corrected_collection = processor.correct(images)

print(f"✓ Processed {corrected_collection.size().getInfo()} images")

# Extract dates
dates = corrected_collection.aggregate_array('system:time_start').getInfo()
print(f"\nProcessed dates:")
for i, timestamp in enumerate(dates[:10], 1):
    date_str = ee.Date(timestamp).format('YYYY-MM-dd').getInfo()
    print(f"  {i}. {date_str}")
if len(dates) > 10:
    print(f"  ... and {len(dates) - 10} more")

# Compute time series statistics
def compute_stats(image):
    stats = image.select('SPM_Nechad2016_665').reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=100,
        bestEffort=True
    )
    return image.set('spm_mean', stats.get('SPM_Nechad2016_665'))

collection_with_stats = corrected_collection.map(compute_stats)

# Get SPM time series
spm_series = collection_with_stats.aggregate_array('spm_mean').getInfo()
dates_formatted = [ee.Date(ts).format('YYYY-MM-dd').getInfo() for ts in dates]

print("\nSPM Time Series (first 10):")
for date, spm in list(zip(dates_formatted, spm_series))[:10]:
    if spm is not None:
        print(f"  {date}: {spm:.2f} mg/L")

print("\n✓ Batch processing complete!")
