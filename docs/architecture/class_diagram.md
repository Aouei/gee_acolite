# Class Diagram

Accurate class and module structure of GEE ACOLITE, based on the actual source code.

---

## Full Package Overview

```mermaid
classDiagram
    namespace gee_acolite {
        class ACOLITE {
            +correct() tuple
            +l1_to_l2() tuple
            +dask_spectrum_fitting() tuple
            +select_lut() tuple
            +compute_pdark() dict
            +estimate_aot_per_lut() dict
            +select_best_model() tuple
            +compute_correction_with_fixed_aot() tuple
            +compute_rhos() Image
            +deglint_alternative() Image
            +get_ancillary_data() dict
            +prepare_query() tuple
            +prepare_earthdata_credentials() dict
        }
        class WaterQuality {
            +compute_water_mask() Image
            +compute_water_bands() Image
            +spm_nechad2016_665() Image
            +spm_nechad2016_704() Image
            +spm_nechad2016_740() Image
            +tur_nechad2016_665() Image
            +chl_oc2() Image
            +chl_oc3() Image
            +chl_re_mishra() Image
            +pSDB_green() Image
            +pSDB_red() Image
            +rrs() Image
        }
        class Bathymetry {
            +optical_deep_water_model() Image
            +calibrate_sdb() dict
            +apply_calibration() Image
            +multi_image() Image
        }
    }

    namespace utils {
        class Search {
            +search() ImageCollection
            +search_list() ImageCollection
            +search_with_cloud_proba() ImageCollection
            +join_s2_with_cloud_prob() ImageCollection
        }
        class L1Convert {
            +l1_to_rrs() ImageCollection
            +DN_to_rrs() Image
            +get_mean_band_angle() Image
            +resample() Image
        }
        class Masks {
            +mask_negative_reflectance() Image
            +toa_mask() Image
            +cirrus_mask() Image
            +non_water() Image
            +add_cloud_bands() Image
            +add_shadow_bands() Image
            +add_cld_shdw_mask() Image
            +cld_shdw_mask() Image
        }
    }

    namespace sensors {
        class Sentinel2 {
            +list SENTINEL2_BANDS
            +dict BAND_BY_SCALE
        }
    }

    ACOLITE --> L1Convert : uses l1_to_rrs
    ACOLITE --> WaterQuality : uses compute_water_bands
    ACOLITE --> Masks : applies masks
    WaterQuality --> Masks : applies masks
    WaterQuality --> Sentinel2 : uses SENTINEL2_BANDS
    L1Convert --> Sentinel2 : uses BAND_BY_SCALE
```

---

## ACOLITE Class — Detailed Methods

```mermaid
classDiagram
    class ACOLITE {
        +correct() tuple
        +l1_to_l2() ImageCollection
        +dask_spectrum_fitting() tuple
        +select_lut() tuple
        +compute_pdark() ndarray
        +estimate_aot_per_lut() dict
        +select_best_model() tuple
        +compute_correction_with_fixed_aot() tuple
        +compute_rhos() Image
        +deglint_alternative() Image
        +get_ancillary_data() dict
    }

    note for ACOLITE "Server-side: correct, l1_to_l2, compute_pdark, compute_rhos, deglint_alternative\nClient-side: estimate_aot_per_lut, select_best_model, dask_spectrum_fitting"
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
graph LR
    P["PRODUCTS dict"]
    P --> A[spm_nechad2016]
    P --> B[spm_nechad2016_704]
    P --> C[spm_nechad2016_740]
    P --> D[tur_nechad2016]
    P --> E[tur_nechad2016_704]
    P --> F[tur_nechad2016_740]
    P --> G[chl_oc2]
    P --> H[chl_oc3]
    P --> I[chl_re_mishra]
    P --> J[pSDB_green]
    P --> K[pSDB_red]
    P --> L["Rrs_B1 to Rrs_B12"]
```

---

## Masking Pipeline

```mermaid
flowchart TD
    A[compute_water_mask] --> B[non_water<br/>B11 less than threshold]
    A --> C[cirrus_mask<br/>B10 less than threshold]
    A --> D[toa_mask<br/>band less than threshold]
    A --> E[add_cld_shdw_mask<br/>optional]
    B --> F[Combined mask Image]
    C --> F
    D --> F
    E --> F

    style A fill:#e1f5ff
    style F fill:#e1ffe1
```

---

## Sentinel-2 Band Configuration

```mermaid
classDiagram
    class Sentinel2Config {
        +list SENTINEL2_BANDS
        +dict BAND_BY_SCALE
    }

    note for Sentinel2Config "SENTINEL2_BANDS: B1 to B12 (13 bands)\nBAND_BY_SCALE: 10m to B2, 20m to B5, 60m to B1"
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
