# Class Diagram

Accurate class and module structure of GEE ACOLITE, based on the actual source code.

---

## Full Package Overview

```mermaid
classDiagram
    class ACOLITE {
        +ModuleType acolite
        +dict settings
        +__init__(acolite, settings)
        +correct(images) tuple
        +l1_to_l2(images, size, settings) tuple
        +dask_spectrum_fitting(image, settings) tuple
        +select_lut(image, settings) tuple
        +compute_pdark(image, settings) dict
        +estimate_aot_per_lut(pdark, lutd, rsrd, ttg, geometry, settings) dict
        +select_best_model(results, lutd, geometry, settings) tuple
        +compute_correction_with_fixed_aot(image, aot, lut_name, settings) tuple
        +compute_rhos(image, am) ee_Image
        +get_ancillary_data(image, settings) dict
        +prepare_query(image) tuple
        +prepare_earthdata_credentials(settings) dict
        +deglint_alternative(image, bands, glint_ave, glint_min, glint_max) ee_Image
    }

    class WaterQuality {
        <<module>>
        +dict PRODUCTS
        +compute_water_mask(image, settings) ee_Image
        +compute_water_bands(image, settings) ee_Image
        +spm_nechad2016_665(image) ee_Image
        +spm_nechad2016_704(image) ee_Image
        +spm_nechad2016_740(image) ee_Image
        +tur_nechad2016_665(image) ee_Image
        +tur_nechad2016_704(image) ee_Image
        +tur_nechad2016_740(image) ee_Image
        +chl_oc2(image) ee_Image
        +chl_oc3(image) ee_Image
        +chl_re_mishra(image) ee_Image
        +ndwi(image) ee_Image
        +pSDB_green(image) ee_Image
        +pSDB_red(image) ee_Image
        +rrs(image) ee_Image
    }

    class Bathymetry {
        <<module>>
        +optical_deep_water_model(model, blue, green, vnir) ee_Image
        +calibrate_sdb(psdb_image, insitu_bathymetry, region, max_depth, num_points, seed, scale) dict
        +apply_calibration(psdb_image, slope, intercept, output_name) ee_Image
        +multi_image(images, band) ee_Image
    }

    class Search {
        <<module>>
        +search(roi, start, end, collection, tile) ee_ImageCollection
        +search_list(roi, starts, ends, collection, tile) ee_ImageCollection
        +search_with_cloud_proba(roi, start, end, collection, tile) ee_ImageCollection
        +join_s2_with_cloud_prob(s2_collection) ee_ImageCollection
    }

    class L1Convert {
        <<module>>
        +l1_to_rrs(images, scale) ee_ImageCollection
        +DN_to_rrs(image) ee_Image
        +get_mean_band_angle(image, angle_name) ee_Image
        +resample(image, band) ee_Image
    }

    class Masks {
        <<module>>
        +mask_negative_reflectance(image, band) ee_Image
        +toa_mask(image, band, threshold) ee_Image
        +cirrus_mask(image, band, threshold) ee_Image
        +non_water(image, band, threshold) ee_Image
        +add_cloud_bands(img, cloud_prob_threshold) ee_Image
        +add_shadow_bands(img, nir_dark_threshold, cloud_proj_distance) ee_Image
        +add_cld_shdw_mask(img, cloud_prob_threshold, nir_dark_threshold, cloud_proj_distance, buffer) ee_Image
        +cld_shdw_mask(img) ee_Image
    }

    class Sentinel2 {
        <<module>>
        +list SENTINEL2_BANDS
        +dict BAND_BY_SCALE
    }

    ACOLITE --> L1Convert : uses l1_to_rrs
    ACOLITE --> WaterQuality : uses compute_water_bands
    ACOLITE --> Masks : uses mask_negative_reflectance
    WaterQuality --> Masks : uses water/cirrus/cloud masks
    WaterQuality --> Sentinel2 : uses SENTINEL2_BANDS
    L1Convert --> Sentinel2 : uses BAND_BY_SCALE
```

---

## ACOLITE Class — Detailed Methods

```mermaid
classDiagram
    class ACOLITE {
        +correct(images) ImageCollection_dict
        +l1_to_l2(images, size, settings) ImageCollection_dict
        +dask_spectrum_fitting(image, settings) Image_list_dict
        +select_lut(image, settings) dict_dict_list
        +compute_pdark(image, settings) dict
        +estimate_aot_per_lut(pdark, lutd, rsrd, ttg, geometry, settings) dict
        +select_best_model(results, lutd, geometry, settings) str_float_str_float
        +compute_correction_with_fixed_aot(image, aot, lut_name, settings) dict_dict_list
        +compute_rhos(image, am) Image
        +deglint_alternative(image, bands, glint_ave, glint_min, glint_max) Image
        +get_ancillary_data(image, settings) dict
    }

    note for ACOLITE "GEE server-side:\ncorrect, l1_to_l2,\ncompute_pdark (reducer),\ncompute_rhos, deglint_alternative\n\nClient-side (numpy/scipy):\nestimate_aot_per_lut,\nselect_best_model,\ndask_spectrum_fitting (orchestration)"
```

### Method Responsibilities

| Method | Execution | Description |
|--------|-----------|-------------|
| `correct()` | Orchestration | Main entry point: calls `l1_to_rrs` then `l1_to_l2` |
| `l1_to_l2()` | Orchestration | Loops over images; calls DSF and `compute_rhos` per image |
| `dask_spectrum_fitting()` | Client | Orchestrates DSF: calls `select_lut` then returns GEE image |
| `select_lut()` | Hybrid | Calls `compute_pdark` (server→client), then estimates AOT (client), then returns atmospheric params |
| `compute_pdark()` | Server → Client | GEE `reduceRegion()` → `getInfo()` — only `getInfo()` per image |
| `estimate_aot_per_lut()` | Client | numpy/scipy LUT interpolation per atmospheric model |
| `select_best_model()` | Client | RMSD/dtau/CV comparison across models |
| `compute_correction_with_fixed_aot()` | Client | Alternative to DSF when AOT is known |
| `compute_rhos()` | Server | GEE image expression: correction formula applied to all bands |
| `deglint_alternative()` | Server | GEE: residual sun glint removal |
| `get_ancillary_data()` | Client | NASA Earthdata API call |

---

## Water Quality Module — PRODUCTS Dictionary

The `PRODUCTS` dict maps product names to their computation functions:

```mermaid
classDiagram
    class PRODUCTS {
        <<dict>>
        spm_nechad2016 --> spm_nechad2016_665
        spm_nechad2016_704 --> spm_nechad2016_704
        spm_nechad2016_740 --> spm_nechad2016_740
        tur_nechad2016 --> tur_nechad2016_665
        tur_nechad2016_704 --> tur_nechad2016_704
        tur_nechad2016_740 --> tur_nechad2016_740
        chl_oc2 --> chl_oc2
        chl_oc3 --> chl_oc3
        chl_re_mishra --> chl_re_mishra
        pSDB_green --> pSDB_green
        pSDB_red --> pSDB_red
        Rrs_B_star --> rrs
    }

    class spm_nechad2016_665 {
        formula: A*R / (1 - R/C)
        band: rhos_B4 (665nm)
        A: 610.94, C: 0.2324
    }

    class chl_oc3 {
        formula: 10^(A + B*x + C*x^2 + D*x^3 + E*x^4)
        x: log10(max(B1,B2) / B3)
    }

    class pSDB_green {
        formula: log(1000*pi*B2) / log(1000*pi*B3)
        bands: rhos_B2, rhos_B3
    }

    class rrs {
        formula: rhos / pi
        bands: all 13 rhos_B* bands
    }
```

---

## Masking Pipeline

```mermaid
classDiagram
    class compute_water_mask {
        <<function>>
        1. non_water(image, band, threshold)
        2. cirrus_mask(image, band, threshold)
        3. toa_mask(image, band, threshold)
        4. add_cld_shdw_mask() [optional]
        returns: combined mask Image
    }

    class non_water {
        band: B11 (SWIR)
        logic: B11 lt threshold
        default threshold: 0.05
    }

    class cirrus_mask {
        band: B10 (1375nm)
        logic: B10 lt threshold
        default threshold: 0.005
    }

    class toa_mask {
        band: configurable
        logic: band lt threshold
        default threshold: 0.3
    }

    class add_cld_shdw_mask {
        uses: S2 Cloud Probability dataset
        steps: cloud, shadow, buffer
    }

    compute_water_mask --> non_water
    compute_water_mask --> cirrus_mask
    compute_water_mask --> toa_mask
    compute_water_mask --> add_cld_shdw_mask
```

---

## Sentinel-2 Band Configuration

```mermaid
classDiagram
    class Sentinel2Config {
        <<module: sensors/sentinel2>>
        +SENTINEL2_BANDS: list
        +BAND_BY_SCALE: dict
    }

    note for Sentinel2Config "SENTINEL2_BANDS = ['B1','B2','B3','B4','B5','B6','B7','B8','B8A','B9','B10','B11','B12']\n\nBAND_BY_SCALE = {\n  10: 'B2',   <- reference for 10m\n  20: 'B5',   <- reference for 20m\n  60: 'B1'    <- reference for 60m\n}"
```

### Band Wavelengths and Resolutions

| Band | Wavelength (nm) | Resolution | Role |
|------|----------------|------------|------|
| B1 | 443 | 60m | Coastal aerosol |
| B2 | 490 | 10m | Blue (pSDB numerator) |
| B3 | 560 | 10m | Green |
| B4 | 665 | 10m | Red (SPM, Turbidity) |
| B5 | 705 | 20m | Red Edge 1 (Chl-a NDCI) |
| B6 | 740 | 20m | Red Edge 2 |
| B7 | 783 | 20m | Red Edge 3 |
| B8 | 842 | 10m | NIR (water mask, shadows) |
| B8A | 865 | 20m | Narrow NIR |
| B9 | 945 | 60m | Water vapour |
| B10 | 1375 | 60m | Cirrus detection |
| B11 | 1610 | 20m | SWIR 1 (water/land mask) |
| B12 | 2190 | 20m | SWIR 2 (glint reference) |

---

## Module Dependency Graph

```mermaid
graph TD
    PKG[gee_acolite package]
    CORR[correction.py]
    WQ[water_quality.py]
    BATH[bathymetry.py]
    SEARCH[utils/search.py]
    L1C[utils/l1_convert.py]
    MSK[utils/masks.py]
    S2[sensors/sentinel2.py]
    AC[ACOLITE submodule]

    PKG --> CORR
    PKG --> WQ
    PKG --> BATH

    CORR --> L1C
    CORR --> MSK
    CORR --> WQ
    CORR --> AC

    WQ --> MSK
    WQ --> S2

    L1C --> S2

    style AC fill:#fef3c7,stroke:#d97706
    style PKG fill:#dbeafe,stroke:#3b82f6
```
