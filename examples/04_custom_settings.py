"""
Example 4: Custom Settings
Demonstrates advanced customization of correction parameters
"""

import ee
import acolite as ac
from gee_acolite import ACOLITE

# Initialize Earth Engine
ee.Initialize()

# Define region
roi = ee.Geometry.Point([-76.7, 38.2])

# Get image
image = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
    .filterBounds(roi) \
    .filterDate('2023-06-15', '2023-06-20') \
    .first()

print("Testing different dark spectrum methods...\n")

# Test 1: Darkest pixel method
print("1. DARKEST PIXEL METHOD")
settings_darkest = {
    'aerosol_correction': 'dark_spectrum',
    'dsf_aot_estimate': 'fixed',
    'dsf_model_selection': 'min_drmsd',
    'dsf_spectrum_option': 'darkest',  # Minimum values
    'dsf_nbands': 3,
    'uoz_default': 0.3,
    'uwv_default': 1.5,
    'pressure_default': 1013.25,
    's2_target_res': 10,
}

processor = ACOLITE(ac, settings_darkest)
result1 = processor.correct(ee.ImageCollection([image])).first()
print("   ✓ Processed with darkest method")

# Test 2: Percentile method
print("\n2. PERCENTILE METHOD (5th percentile)")
settings_percentile = {
    'aerosol_correction': 'dark_spectrum',
    'dsf_aot_estimate': 'fixed',
    'dsf_model_selection': 'min_drmsd',
    'dsf_spectrum_option': 'percentile',  # Use percentile
    'dsf_percentile': 5,  # 5th percentile
    'dsf_nbands': 3,
    'uoz_default': 0.3,
    'uwv_default': 1.5,
    'pressure_default': 1013.25,
    's2_target_res': 20,  # Different resolution
}

processor = ACOLITE(ac, settings_percentile)
result2 = processor.correct(ee.ImageCollection([image])).first()
print("   ✓ Processed with percentile method")

# Test 3: Different model selection
print("\n3. COEFFICIENT OF VARIATION MODEL SELECTION")
settings_cv = {
    'aerosol_correction': 'dark_spectrum',
    'dsf_aot_estimate': 'fixed',
    'dsf_model_selection': 'taua_cv',  # CV instead of RMSD
    'dsf_spectrum_option': 'darkest',
    'dsf_nbands': 2,
    'uoz_default': 0.3,
    'uwv_default': 1.5,
    'pressure_default': 1013.25,
    's2_target_res': 10,
}

processor = ACOLITE(ac, settings_cv)
result3 = processor.correct(ee.ImageCollection([image])).first()
print("   ✓ Processed with CV model selection")

# Test 4: With glint correction
print("\n4. WITH RESIDUAL GLINT CORRECTION")
settings_glint = {
    'aerosol_correction': 'dark_spectrum',
    'dsf_aot_estimate': 'fixed',
    'dsf_model_selection': 'min_drmsd',
    'dsf_spectrum_option': 'darkest',
    'dsf_nbands': 2,
    'uoz_default': 0.3,
    'uwv_default': 1.5,
    'pressure_default': 1013.25,
    's2_target_res': 10,
    'dsf_residual_glint_correction': True,
    'dsf_residual_glint_correction_method': 'alternative',
    'glint_mask_rhos_threshold': 0.05,
}

processor = ACOLITE(ac, settings_glint)
result4 = processor.correct(ee.ImageCollection([image])).first()
print("   ✓ Processed with glint correction")

# Compare reflectances at a sample point
sample_point = roi
band = 'rhos_B3'  # Green band

print(f"\nComparison of {band} at sample point:")

for i, (result, method) in enumerate([
    (result1, "Darkest"),
    (result2, "Percentile"),
    (result3, "CV Selection"),
    (result4, "With Glint Correction")
], 1):
    value = result.select(band).sample(
        region=sample_point, scale=10, numPixels=1
    ).first().get(band).getInfo()
    print(f"  {i}. {method:20s}: {value:.4f}")

print("\n✓ Custom settings comparison complete!")
