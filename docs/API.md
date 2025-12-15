# API Documentation

Comprehensive API reference for GEE ACOLITE.

## Table of Contents

1. [Main Classes](#main-classes)
2. [Correction Module](#correction-module)
3. [Water Quality Module](#water-quality-module)
4. [Utilities](#utilities)
5. [Sensors](#sensors)

---

## Main Classes

### `ACOLITE`

Main atmospheric correction processor class.

**Location:** `gee_acolite.correction`

```python
from gee_acolite import ACOLITE
```

#### Constructor

```python
ACOLITE(acolite: ModuleType, settings: str | dict)
```

**Parameters:**
- `acolite`: The ACOLITE module (import as `import acolite as ac`)
- `settings`: Processing settings (dict or path to settings file)

**Returns:** ACOLITE processor instance

#### Methods

##### `correct(images: ee.ImageCollection) -> Tuple[ee.ImageCollection, dict]`

Apply atmospheric correction to image collection.

**Parameters:**
- `images`: Input Sentinel-2 image collection (L1C)

**Returns:**
- `corrected_images`: Atmospherically corrected image collection
- `settings`: Final settings used for processing

**Example:**
```python
processor = ACOLITE(ac, settings)
corrected, final_settings = processor.correct(images)
```

---

## Correction Module

### Dark Spectrum Fitting

The package implements three methods for extracting dark spectrum:

#### 1. Darkest Pixel (`darkest`)
Uses minimum pixel value per band.

```python
settings = {
    'dsf_spectrum_option': 'darkest',
}
```

#### 2. Percentile (`percentile`)
Uses Nth percentile of pixel values.

```python
settings = {
    'dsf_spectrum_option': 'percentile',
    'dsf_percentile': 5,  # Use 5th percentile
}
```

#### 3. Intercept (`intercept`)
Uses linear regression intercept.

```python
settings = {
    'dsf_spectrum_option': 'intercept',
    'dsf_intercept_pixels': 100,  # Number of darkest pixels
}
```

### Model Selection

Three criteria for selecting best atmospheric model:

#### 1. Minimum RMSD (`min_drmsd`)
Minimum root mean square deviation between observed and modeled reflectance.

```python
settings = {
    'dsf_model_selection': 'min_drmsd',
    'dsf_nbands_fit': 2,  # Bands used for validation
}
```

#### 2. Minimum Delta Tau (`min_dtau`)
Minimum difference in AOT between two darkest bands.

```python
settings = {
    'dsf_model_selection': 'min_dtau',
}
```

#### 3. Coefficient of Variation (`taua_cv`)
Minimum coefficient of variation of AOT estimates.

```python
settings = {
    'dsf_model_selection': 'taua_cv',
}
```

---

## Water Quality Module

### `compute_water_bands(image: ee.Image, settings: dict) -> ee.Image`

Compute water quality parameters.

**Location:** `gee_acolite.water_quality`

**Parameters:**
- `image`: Atmospherically corrected image with `rhos_*` bands
- `settings`: Settings dict with `l2w_parameters` key

**Returns:** Image with added water quality bands

**Example:**
```python
from gee_acolite import compute_water_bands

settings = {
    'l2w_parameters': ['spm_nechad2016', 'chl_oc2', 'ndwi']
}

result = compute_water_bands(corrected_image, settings)
```

### Available Products

Configure in settings with `l2w_parameters`:

#### Suspended Particulate Matter (SPM)
- `spm_nechad2016`: SPM at 665nm (Nechad et al. 2016)
- `spm_nechad2016_704`: SPM at 704nm
- `spm_nechad2016_740`: SPM at 740nm

#### Turbidity
- `tur_nechad2016`: Turbidity at 665nm (Nechad et al. 2016)
- `tur_nechad2016_704`: Turbidity at 704nm
- `tur_nechad2016_740`: Turbidity at 740nm

#### Chlorophyll-a
- `chl_oc2`: OC2 algorithm (O'Reilly et al. 1998)
- `chl_oc3`: OC3 algorithm (O'Reilly et al. 2000)
- `chl_re_mishra`: Red-edge algorithm (Mishra & Mishra 2012)

#### Bathymetry
- `pSDB_green`: Pseudo-satellite derived bathymetry (green band)
- `pSDB_red`: Pseudo-satellite derived bathymetry (red band)

#### Indices
- `ndwi`: Normalized Difference Water Index
- `Rrs_*`: Remote sensing reflectance for all bands

---

## Utilities

### L1 Conversion

**Location:** `gee_acolite.utils.l1_convert`

#### `l1_to_rrs(images: ee.ImageCollection, scale: int) -> ee.ImageCollection`

Convert L1C DN to TOA reflectance.

**Parameters:**
- `images`: Sentinel-2 L1C image collection
- `scale`: Target resolution (10, 20, or 60m)

**Returns:** TOA reflectance image collection with geometry properties

### Masks

**Location:** `gee_acolite.utils.masks`

#### `mask_negative_reflectance(image: ee.Image, band: str) -> ee.Image`

Mask negative reflectance values.

#### `non_water(image: ee.Image, threshold: float) -> ee.Image`

Create non-water mask based on SWIR reflectance.

#### `add_cld_shdw_mask(image: ee.Image, ...) -> ee.Image`

Add cloud and shadow mask using S2 Cloud Probability.

**Parameters:**
- `cloud_prob_threshold`: Cloud probability threshold (0-100)
- `nir_dark_threshold`: NIR dark pixel threshold
- `cloud_proj_distance`: Shadow projection distance (km)
- `buffer`: Cloud buffer distance (m)

### Search

**Location:** `gee_acolite.utils.search`

#### `search(roi: ee.Geometry, start: str, end: str, ...) -> ee.ImageCollection`

Search for Sentinel-2 images.

**Parameters:**
- `roi`: Region of interest
- `start`: Start date ('YYYY-MM-DD')
- `end`: End date ('YYYY-MM-DD')
- `collection`: Collection name (default: 'S2_HARMONIZED')
- `tile`: Optional tile ID filter

#### `search_with_cloud_proba(...) -> ee.ImageCollection`

Search and join with Cloud Probability data.

---

## Sensors

### Sentinel-2 Constants

**Location:** `gee_acolite.sensors.sentinel2`

```python
from gee_acolite.sensors import SENTINEL2_BANDS, BAND_BY_SCALE

# All Sentinel-2 bands
print(SENTINEL2_BANDS)
# ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']

# Reference band by resolution
print(BAND_BY_SCALE)
# {10: 'B2', 20: 'B5', 60: 'B1'}
```

---

## Configuration Settings

### Complete Settings Example

```python
settings = {
    # Correction method
    'aerosol_correction': 'dark_spectrum',
    'dsf_aot_estimate': 'fixed',
    
    # Dark spectrum options
    'dsf_spectrum_option': 'darkest',  # 'darkest', 'percentile', 'intercept'
    'dsf_percentile': 5,  # For percentile method
    'dsf_intercept_pixels': 100,  # For intercept method
    
    # Model selection
    'dsf_model_selection': 'min_drmsd',  # 'min_drmsd', 'min_dtau', 'taua_cv'
    'dsf_nbands': 2,  # Bands for AOT estimation
    'dsf_nbands_fit': 2,  # Bands for model validation
    
    # Atmospheric parameters (defaults)
    'uoz_default': 0.3,  # Ozone (cm-atm)
    'uwv_default': 1.5,  # Water vapor (g/cm²)
    'pressure_default': 1013.25,  # Pressure (hPa)
    'wind_default': 2.0,  # Wind speed (m/s)
    
    # Processing options
    's2_target_res': 10,  # Target resolution (m)
    'dsf_residual_glint_correction': True,  # Enable glint correction
    'dsf_residual_glint_correction_method': 'alternative',
    'glint_mask_rhos_threshold': 0.05,
    
    # Water quality products
    'l2w_parameters': [
        'spm_nechad2016',
        'chl_oc2',
        'ndwi',
    ],
    
    # Masking
    'l2w_mask_threshold': 0.05,  # NIR threshold for water mask
    'l2w_mask_negative_rhow': True,  # Mask negative reflectance
}
```

---

## Error Handling

Common errors and solutions:

### `ModuleNotFoundError: No module named 'acolite'`

**Solution:** Install ACOLITE from source:
```bash
git clone https://github.com/acolite/acolite.git
cd acolite
pip install -e .
```

### `ee.ee_exception.EEException: User memory limit exceeded`

**Solution:** Reduce processing area size or filter to fewer images.

### Negative reflectance values

**Solution:** Enable negative masking:
```python
settings = {'l2w_mask_negative_rhow': True}
```

---

## References

1. Vanhellemont, Q., & Ruddick, K. (2019). Adaptation of the dark spectrum fitting atmospheric correction for aquatic applications of the Landsat and Sentinel-2 archives. *Remote Sensing of Environment*, 225, 175-192.

2. Nechad, B., Ruddick, K., & Park, Y. (2016). Calibration and validation of a generic multisensor algorithm for mapping of total suspended matter in turbid waters. *Remote Sensing of Environment*, 159, 44-52.

3. O'Reilly, J. E., et al. (1998). Ocean color chlorophyll algorithms for SeaWiFS. *Journal of Geophysical Research*, 103(C11), 24937-24953.
