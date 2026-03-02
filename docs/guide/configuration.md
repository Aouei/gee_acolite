# Configuration

Complete reference for all settings parameters accepted by `ACOLITE(ac, settings)`.

Settings can be provided as a **Python dict** or as a path to an **ACOLITE settings file** (`.txt`).

```python
# Dict approach
ac_gee = ACOLITE(ac, {'s2_target_res': 10, 'dsf_spectrum_option': 'darkest'})

# File approach
ac_gee = ACOLITE(ac, 'path/to/settings.txt')
```

Settings files follow the ACOLITE format: `key=value` pairs, one per line.

---

## Spatial Resolution

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `s2_target_res` | `int` | `10` | Target spatial resolution in metres. All bands resampled to this. Valid: `10`, `20`, `60`. |

---

## Dark Spectrum Fitting (DSF)

These parameters control how the **single global AOT** is estimated per image.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dsf_spectrum_option` | `str` | `'darkest'` | Dark spectrum extraction method: `'darkest'`, `'percentile'`, or `'intercept'` |
| `dsf_percentile` | `float` | `1` | Percentile when `dsf_spectrum_option='percentile'` |
| `dsf_intercept_pixels` | `int` | `1000` | Darkest pixels for regression when `dsf_spectrum_option='intercept'` |
| `dsf_nbands` | `int` | `2` | Number of darkest bands used for AOT fitting |
| `dsf_nbands_fit` | `int` | `3` | Bands used for RMSD model validation |
| `dsf_model_selection` | `str` | `'min_drmsd'` | Model selection criterion: `'min_drmsd'`, `'min_dtau'`, or `'taua_cv'` |

### Dark Spectrum Options

| Option | Description | When to use |
|--------|-------------|-------------|
| `darkest` | 0th percentile across all pixels | Clear water, fast (recommended) |
| `percentile` | Nth percentile (configurable) | Slightly turbid or coastal waters |
| `intercept` | Linear regression y-intercept on darkest N pixels | Heterogeneous scenes |

### Model Selection Criteria

| Criterion | Description |
|-----------|-------------|
| `min_drmsd` | Minimise RMSD between observed and modelled TOA reflectance (recommended) |
| `min_dtau` | Minimise AOT difference between the two darkest bands |
| `taua_cv` | Minimise coefficient of variation of AOT estimates |

---

## Fixed AOT (Skip DSF)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dsf_fixed_aot` | `float` | `None` | Fixed AOT at 550 nm. If set, DSF is skipped entirely. |
| `dsf_fixed_lut` | `str` | `None` | LUT model name. Required when `dsf_fixed_aot` is set. |

```python
settings = {
    'dsf_fixed_aot': 0.08,
    'dsf_fixed_lut': 'ACOLITE-LUT-202110081200-MOD1',
}
```

---

## Atmospheric Parameters

| Parameter | Unit | Default | Typical range | Description |
|-----------|------|---------|--------------|-------------|
| `pressure` | hPa | `1013.25` | 980–1040 | Surface atmospheric pressure |
| `uoz` | cm-atm | `0.3` | 0.2–0.45 | Total ozone column |
| `uwv` | g/cm²  | `1.5` | 0.5–5.0 | Atmospheric water vapour |
| `wind` | m/s | `3.0` | 0–20 | Wind speed (affects sea surface roughness) |

### Typical Water Vapour by Climate Zone

| Climate | `uwv` (g/cm²) |
|---------|--------------|
| Arctic / polar | 0.3–0.5 |
| Temperate dry | 0.8–1.5 |
| Temperate humid | 1.5–2.5 |
| Subtropical | 2.0–3.5 |
| Tropical | 3.5–5.0 |

```python
import numpy as np
altitude_m = 500
settings['pressure'] = 1013.25 * np.exp(-altitude_m / 8000)
```

---

## Ancillary Data (NASA Earthdata)

Automatically retrieve per-image atmospheric parameters from NASA Earthdata.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ancillary_data` | `bool` | `False` | Fetch atmospheric parameters from NASA Earthdata per image |
| `EARTHDATA_u` | `str` | `None` | NASA Earthdata username |
| `EARTHDATA_p` | `str` | `None` | NASA Earthdata password |

!!! tip
    When `ancillary_data=True`, the manually specified `pressure`, `uoz`, `uwv`, and `wind` are overridden.

---

## Water Quality Products

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `l2w_parameters` | `list[str]` | `[]` | List of products to compute after atmospheric correction |

### Available Products

| Key | Output band | Description |
|-----|-------------|-------------|
| `spm_nechad2016` | `spm_nechad2016` | SPM at 665 nm — Nechad 2016 (mg/L) |
| `spm_nechad2016_704` | `spm_nechad2016_704` | SPM at 704 nm (mg/L) |
| `spm_nechad2016_740` | `spm_nechad2016_740` | SPM at 740 nm (mg/L) |
| `tur_nechad2016` | `tur_nechad2016` | Turbidity at 665 nm — Nechad 2016 (FNU) |
| `tur_nechad2016_704` | `tur_nechad2016_704` | Turbidity at 704 nm (FNU) |
| `tur_nechad2016_740` | `tur_nechad2016_740` | Turbidity at 740 nm (FNU) |
| `chl_oc2` | `chl_oc2` | Chlorophyll-a OC2 2-band algorithm (mg/m³) |
| `chl_oc3` | `chl_oc3` | Chlorophyll-a OC3 3-band algorithm (mg/m³) |
| `chl_re_mishra` | `chl_re_mishra` | Chlorophyll-a NDCI red-edge — Mishra (mg/m³) |
| `pSDB_green` | `pSDB_green` | Pseudo-SDB: log(1000*pi*B2) / log(1000*pi*B3) |
| `pSDB_red` | `pSDB_red` | Pseudo-SDB: log(1000*pi*B2) / log(1000*pi*B4) |
| `Rrs_B*` | `Rrs_B1` … `Rrs_B12` | Remote sensing reflectance: rhos / pi (sr^-1) |

---

## Quality Masking

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `l2w_mask_threshold` | `float` | `0.05` | SWIR B11 threshold. Pixels with B11 >= threshold masked as land. |
| `l2w_mask_cirrus_threshold` | `float` | `0.005` | B10 (1375 nm) cirrus cloud threshold |
| `l2w_mask_high_toa_threshold` | `float` | `0.3` | TOA reflectance cloud threshold |
| `s2_cloud_proba` | `bool` | `False` | Use Sentinel-2 Cloud Probability dataset for enhanced masking |
| `s2_cloud_proba__cloud_threshold` | `int` | `50` | Cloud probability threshold (0–100) |
| `s2_cloud_proba__nir_dark_threshold` | `float` | `0.15` | NIR threshold for shadow detection |
| `s2_cloud_proba__cloud_proj_distance` | `float` | `10` | Shadow projection distance (km) |
| `s2_cloud_proba__buffer` | `int` | `50` | Buffer around detected cloud/shadow (m) |

### Mask Presets

```python
# Conservative: fewer masked pixels
conservative = {
    'l2w_mask_threshold': 0.02,
    'l2w_mask_cirrus_threshold': 0.01,
    'l2w_mask_high_toa_threshold': 0.4,
}

# Standard (default)
standard = {
    'l2w_mask_threshold': 0.05,
    'l2w_mask_cirrus_threshold': 0.005,
    'l2w_mask_high_toa_threshold': 0.3,
}

# Strict: higher quality, less data
strict = {
    'l2w_mask_threshold': 0.08,
    'l2w_mask_cirrus_threshold': 0.003,
    'l2w_mask_high_toa_threshold': 0.2,
    's2_cloud_proba': True,
    's2_cloud_proba__cloud_threshold': 35,
}
```

---

## Glint Correction

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dsf_residual_glint_correction` | `bool` | `False` | Apply residual sun glint correction after DSF |
| `dsf_residual_glint_correction_method` | `str` | `'alternative'` | Glint correction method (currently only `'alternative'`) |
| `glint_mask_rhos_threshold` | `float` | `0.05` | Max surface reflectance for glint-free reference pixel |

---

## Scenario Presets

### Coastal Clear Waters

```python
coastal_clear = {
    's2_target_res': 10,
    'dsf_spectrum_option': 'darkest',
    'dsf_model_selection': 'min_drmsd',
    'pressure': 1013.25, 'wind': 2.0, 'uoz': 0.3, 'uwv': 1.5,
    'l2w_mask_threshold': 0.05,
    'l2w_parameters': ['spm_nechad2016', 'chl_oc3', 'pSDB_green'],
}
```

### Turbid Estuaries

```python
turbid_waters = {
    's2_target_res': 10,
    'dsf_spectrum_option': 'percentile',
    'dsf_percentile': 5,
    'dsf_model_selection': 'min_drmsd',
    'pressure': 1013.25, 'wind': 3.0, 'uoz': 0.3, 'uwv': 2.0,
    'l2w_mask_threshold': -0.1,
    'l2w_mask_high_toa_threshold': 0.4,
    'l2w_parameters': ['spm_nechad2016', 'tur_nechad2016', 'spm_nechad2016_704'],
}
```

### Inland Lakes

```python
inland_waters = {
    's2_target_res': 10,
    'dsf_spectrum_option': 'darkest',
    'dsf_model_selection': 'taua_cv',
    'pressure': 950.0, 'wind': 1.0, 'uoz': 0.3, 'uwv': 1.0,
    'l2w_mask_threshold': 0.0,
    'l2w_parameters': ['chl_oc3', 'chl_re_mishra', 'tur_nechad2016'],
}
```

---

## References

- [ACOLITE Wiki](https://github.com/acolite/acolite/wiki)
- [Water Quality API](../api/water_quality.md)
- [GEE Integration](../architecture/gee_integration.md)
