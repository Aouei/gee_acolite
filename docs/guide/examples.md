# Examples

Practical examples covering the main use cases of GEE ACOLITE: atmospheric correction workflows and satellite-derived bathymetry.

---

## Example 1 — Basic Atmospheric Correction

Correct a single Sentinel-2 scene and compute water quality products.

```python
import ee
import acolite as ac
from gee_acolite import ACOLITE
from gee_acolite.utils.search import search

ee.Initialize(project='your-cloud-project-id')

# --- 1. Search ---
roi = ee.Geometry.Rectangle([-0.40, 39.27, -0.28, 39.38])
images = search(roi, '2023-07-15', '2023-07-16', tile='30SYJ')
print(f"Images found: {images.size().getInfo()}")

# --- 2. Configure ---
settings = {
    's2_target_res': 10,
    'dsf_spectrum_option': 'darkest',
    'dsf_model_selection': 'min_drmsd',
    'dsf_nbands': 2,
    'pressure': 1013.25,
    'uoz': 0.3,
    'uwv': 1.5,
    'wind': 2.5,
    'l2w_parameters': [
        'spm_nechad2016',       # SPM at 665 nm (mg/L)
        'spm_nechad2016_704',   # SPM at 704 nm (mg/L)
        'tur_nechad2016',       # Turbidity at 665 nm (FNU)
        'chl_oc3',              # Chlorophyll-a OC3 (mg/m3)
        'chl_re_mishra',        # Chlorophyll-a NDCI red-edge
        'pSDB_green',           # Pseudo-SDB blue/green
        'pSDB_red',             # Pseudo-SDB blue/red
    ],
}

# --- 3. Correct ---
ac_gee = ACOLITE(ac, settings)
corrected, final_settings = ac_gee.correct(images)

# --- 4. Inspect bands ---
bands = corrected.first().bandNames().getInfo()
print("Output bands:", bands)
# Example: ['rhot_B1', ..., 'rhot_B12', 'rhos_B1', ..., 'rhos_B12',
#           'spm_nechad2016', 'tur_nechad2016', 'chl_oc3', 'pSDB_green', ...]
```

---

## Example 2 — Fixed AOT (Skip DSF)

Use a known AOT and LUT instead of running the dark spectrum fitting. Useful when you have external AOT estimates (e.g., AERONET).

```python
settings = {
    's2_target_res': 10,
    'dsf_fixed_aot': 0.05,
    'dsf_fixed_lut': 'ACOLITE-LUT-202110081200-MOD1',
    'pressure': 1013.25,
    'uoz': 0.3,
    'uwv': 1.5,
    'wind': 2.5,
    'l2w_parameters': ['spm_nechad2016', 'chl_oc3'],
}

ac_gee = ACOLITE(ac, settings)
corrected, _ = ac_gee.correct(images)
```

!!! note "Available LUT names"
    LUT names depend on the ACOLITE version and are loaded from `ACOLITE/data/LUT/`.
    Use `acolite.aerlut.import_luts('S2A_MSI', settings)` to list available models.

---

## Example 3 — With Ancillary Atmospheric Data

Retrieve pressure, ozone, and water vapour from NASA Earthdata automatically for each image.

```python
settings = {
    's2_target_res': 10,
    'dsf_spectrum_option': 'darkest',
    'dsf_model_selection': 'min_drmsd',
    'ancillary_data': True,
    'EARTHDATA_u': 'your_username',
    'EARTHDATA_p': 'your_password',
    'l2w_parameters': ['spm_nechad2016', 'chl_oc3'],
}

ac_gee = ACOLITE(ac, settings)
corrected, _ = ac_gee.correct(images)
```

---

## Example 4 — Time Series with Cloud Probability Masking

Process a multi-month time series with enhanced cloud and shadow masking.

```python
from gee_acolite.utils.search import search_with_cloud_proba
import pandas as pd
import datetime

roi = ee.Geometry.Rectangle([-0.40, 39.27, -0.28, 39.38])
images = search_with_cloud_proba(roi, '2023-01-01', '2023-12-31', tile='30SYJ')
images = images.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
print(f"Found {images.size().getInfo()} images")

settings = {
    's2_target_res': 10,
    'dsf_spectrum_option': 'darkest',
    'dsf_model_selection': 'min_drmsd',
    'pressure': 1013.25,
    'uoz': 0.3,
    'uwv': 1.5,
    'wind': 3.0,
    's2_cloud_proba': True,
    's2_cloud_proba__cloud_threshold': 50,
    's2_cloud_proba__nir_dark_threshold': 0.15,
    's2_cloud_proba__cloud_proj_distance': 10,
    's2_cloud_proba__buffer': 50,
    'l2w_parameters': ['spm_nechad2016', 'chl_oc3'],
}

ac_gee = ACOLITE(ac, settings)
corrected, final_settings = ac_gee.correct(images)

# Extract SPM time series at a point
point = ee.Geometry.Point([-0.35, 39.32])

def extract_spm(image):
    val = image.select('spm_nechad2016').reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point.buffer(100),
        scale=10,
    )
    return image.set('spm_mean', val.get('spm_nechad2016'))

ts = corrected.map(extract_spm)
dates  = ts.aggregate_array('system:time_start').getInfo()
values = ts.aggregate_array('spm_mean').getInfo()

df = pd.DataFrame({
    'date': [datetime.datetime.fromtimestamp(d / 1000) for d in dates],
    'spm_mg_L': values,
}).sort_values('date')
print(df.head())
```

---

## Example 5 — Download Corrected Images as GeoTIFF

Download corrected scenes locally using [geemap](https://geemap.org). Two options: a single best-pixel mosaic or one file per scene.

### 5.1 — Single mosaic

```python
import geemap
from datetime import datetime, timedelta
from gee_acolite.utils.search import search_list
from gee_acolite import bathymetry

bands = [
    'Rrs_B1', 'Rrs_B2', 'Rrs_B3', 'Rrs_B4',
    'Rrs_B5', 'Rrs_B6', 'Rrs_B7', 'Rrs_B8', 'Rrs_B8A',
    'Rrs_B11', 'Rrs_B12',
    'pSDB_green', 'pSDB_red',
    'tur_nechad2016', 'chl_oc3',
]

roi    = ee.Geometry.Rectangle([-0.40, 39.27, -0.28, 39.38])
starts = ['2018-09-19', '2018-10-04', '2018-10-17']
ends   = [
    (datetime.strptime(d, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    for d in starts
]

corrector    = ACOLITE(ac, settings)
collection   = search_list(roi, starts, ends, tile='30SYJ')
corrected, _ = corrector.correct(collection)

mosaic = bathymetry.multi_image(corrected)

geemap.download_ee_image(
    image=mosaic.select(bands),
    filename='output/mosaic.tif',
    region=roi,
    crs='EPSG:32630',
    scale=10,
    dtype='float32',
)
```

!!! tip "Masked pixels and NaN"
    GEE exports masked pixels as `nodata`. When opening the result with rasterio or xarray, use `masked=True` or set `nodata=float('nan')` to avoid treating them as valid zeros or infinities.

### 5.2 — One file per scene

```python
filenames = [f'{d.replace("-", "_")}.tif' for d in starts]

geemap.download_ee_image_collection(
    collection=corrected.select(bands),
    out_dir='output/scenes/',
    filenames=filenames,
    region=roi,
    crs='EPSG:32630',
    scale=10,
    dtype='float32',
)
```

---

## Example 6 — Satellite-Derived Bathymetry (Full Workflow)

End-to-end bathymetry: pSDB computation, optical filtering, and calibration against in-situ depths.

### 6.1 — Compute pSDB

```python
from gee_acolite.bathymetry import multi_image, optical_deep_water_model
from gee_acolite.bathymetry import calibrate_sdb, apply_calibration

roi = ee.Geometry.Rectangle([-0.40, 39.27, -0.28, 39.38])
images = search(roi, '2022-06-01', '2022-09-30', tile='30SYJ')
images = images.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))

settings = {
    's2_target_res': 10,
    'dsf_spectrum_option': 'darkest',
    'dsf_model_selection': 'min_drmsd',
    'pressure': 1013.25,
    'uoz': 0.3,
    'uwv': 1.5,
    'wind': 2.5,
    'l2w_parameters': ['pSDB_green', 'pSDB_red'],
}

ac_gee = ACOLITE(ac, settings)
corrected, _ = ac_gee.correct(images)
```

### 6.2 — Best-Pixel Mosaic

```python
# Quality mosaic: selects best pixel across all scenes
psdb_mosaic_green = multi_image(corrected, band='pSDB_green')
psdb_mosaic_red   = multi_image(corrected, band='pSDB_red')
```

`multi_image()` uses `ee.ImageCollection.qualityMosaic(band)` to pick the highest-value pixel per location, corresponding to the clearest water observation.

### 6.3 — Optical Deep-Water Filter

Removes pixels that are optically too deep or turbid for reliable depth retrieval.

```python
blue_mosaic  = corrected.select('rhos_B2').mosaic()
green_mosaic = corrected.select('rhos_B3').mosaic()
nir_mosaic   = corrected.select('rhos_B8').mosaic()

psdb_filtered = optical_deep_water_model(
    model=psdb_mosaic_green,
    blue=blue_mosaic,
    green=green_mosaic,
    vnir=nir_mosaic,
)
```

Filtering criteria applied:

| Criterion | Equation | Purpose |
|-----------|----------|---------|
| Clear water | `B2 > 0.003` AND `B3 > 0.003` | Remove optically shallow pixels |
| Turbid depth limit | `Ymax = -0.251 * ln(NIR) + 0.8` | Limit depth in turbid water |

### 6.4 — Calibrate Against In-Situ Data

```python
# Load in-situ bathymetry (GEE Image with depth values in meters)
insitu = ee.Image('projects/your-project/assets/insitu_bathymetry_2022')

calibration = calibrate_sdb(
    psdb_image=psdb_filtered,
    insitu_bathymetry=insitu,
    region=roi,
    max_depth=15.0,     # Maximum depth considered for calibration
    num_points=50,      # Number of random calibration points
    seed=42,
    scale=10,
)

print(f"Slope:     {calibration['slope']:.4f}")
print(f"Intercept: {calibration['intercept']:.4f}")
print(f"Pearson R: {calibration['correlation']:.4f}")

# Apply linear calibration: depth = slope * pSDB + intercept
sdb_map = apply_calibration(
    psdb_image=psdb_filtered,
    slope=calibration['slope'],
    intercept=calibration['intercept'],
    output_name='depth_m',
)
```

### 6.5 — Visualize and Export

```python
import geemap

Map = geemap.Map()
Map.centerObject(roi, 12)

Map.addLayer(
    sdb_map.select('depth_m'),
    {'min': 0, 'max': 15, 'palette': ['navy', 'blue', 'cyan', 'white']},
    'SDB Depth (m)',
)
Map.addLayer(
    psdb_mosaic_green,
    {'min': 1.0, 'max': 1.35, 'palette': ['white', 'cyan', 'blue', 'navy']},
    'pSDB green (raw)',
)
Map

# Export
task = ee.batch.Export.image.toDrive(
    image=sdb_map.clip(roi),
    description='sdb_calibrated',
    folder='GEE_ACOLITE',
    fileNamePrefix='sdb_2022_summer',
    region=roi,
    scale=10,
    maxPixels=1e9,
    crs='EPSG:32630',
)
task.start()
```

---

## Example 7 — Multi-Year Bathymetry Mosaic

Combine summer seasons from multiple years for maximum benthic coverage.

```python
from gee_acolite.bathymetry import multi_image

def process_summer(year, roi, tile):
    images = search(roi, f'{year}-06-01', f'{year}-09-30', tile=tile)
    images = images.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))
    if images.size().getInfo() == 0:
        return None

    settings = {
        's2_target_res': 10,
        'dsf_spectrum_option': 'darkest',
        'dsf_model_selection': 'min_drmsd',
        'pressure': 1013.25, 'uoz': 0.3, 'uwv': 1.5, 'wind': 2.5,
        'l2w_parameters': ['pSDB_green', 'pSDB_red'],
    }
    ac_gee = ACOLITE(ac, settings)
    corrected, _ = ac_gee.correct(images)
    return corrected

# Process 2020-2023 summer seasons
all_collections = [
    col for year in [2020, 2021, 2022, 2023]
    if (col := process_summer(year, roi, '30SYJ')) is not None
]

combined = ee.ImageCollection(all_collections).flatten()
best_green = multi_image(combined, band='pSDB_green')
best_red   = multi_image(combined, band='pSDB_red')

print("Multi-year mosaic created.")
```