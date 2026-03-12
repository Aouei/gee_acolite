# Class Diagram

Accurate class and module structure of GEE ACOLITE. Organised by **where each component lives**: client (local Python process) or server (GEE cloud).

---

## Client-Side Components

These classes and functions run in the **local Python process**. They block until complete and cannot be deferred to GEE.

```mermaid
classDiagram
    namespace gee_acolite {
        class ACOLITE {
            +get_ancillary_data() dict
            +select_lut() tuple
            +estimate_aot_per_lut() dict
            +select_best_model() tuple
            +compute_correction_with_fixed_aot() tuple
            +dask_spectrum_fitting() dict
        }
    }

    namespace acolite_pkg {
        class AcoliteLUTs {
            +import_luts() dict
            +import_rsky_luts() dict
            +gas_transmittance() ndarray
            +rsr_dict() dict
        }
        class AcoliteMisc {
            +settings_parse() dict
            +ancillary_get() dict
        }
    }

    namespace numeric {
        class NumPySciPy {
            +interp() ndarray
            +minimize() OptimizeResult
        }
    }

    ACOLITE --> AcoliteLUTs : loads LUTs + gas transmittance
    ACOLITE --> AcoliteMisc : parses settings + ancillary
    ACOLITE --> NumPySciPy : AOT interpolation + model selection
```

### Client Method Responsibilities

| Method | Role |
|--------|------|
| `__load_settings()` | Parse settings via `acolite.acolite.settings.parse()` |
| `get_ancillary_data()` | Fetch pressure/wind/ozone from NASA Earthdata |
| `select_lut()` | Load LUT files from disk for each atmospheric model |
| `estimate_aot_per_lut()` | `np.interp()` — AOT at 550 nm per model, per band |
| `select_best_model()` | RMSD / dtau / CV comparison → best LUT + fixed AOT |
| `compute_correction_with_fixed_aot()` | Extract `romix`, `dutott`, `astot`, `tg` from best LUT |
| `dask_spectrum_fitting()` | Orchestrates DSF: calls `select_lut` → returns atmospheric params |

---

## Server-Side Components

These classes and functions return `ee.Image` / `ee.ImageCollection`. They are **lazy** — no computation runs until `.getInfo()`, `.export()`, or tile rendering is triggered.

```mermaid
classDiagram
    namespace gee_acolite_server {
        class ACOLITE_GEE {
            +correct() tuple
            +l1_to_l2() ImageCollection
            +compute_pdark() dict
            +compute_rhos() Image
            +deglint_alternative() Image
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

    namespace utils_server {
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
        class Search {
            +search() ImageCollection
            +search_list() ImageCollection
            +search_with_cloud_proba() ImageCollection
            +join_s2_with_cloud_prob() ImageCollection
        }
    }

    namespace sensors {
        class Sentinel2 {
            +list SENTINEL2_BANDS
            +dict BAND_BY_SCALE
        }
    }

    ACOLITE_GEE --> L1Convert : l1_to_rrs()
    ACOLITE_GEE --> WaterQuality : compute_water_bands()
    ACOLITE_GEE --> Masks : masking pipeline
    WaterQuality --> Masks : water mask
    WaterQuality --> Sentinel2 : SENTINEL2_BANDS
    L1Convert --> Sentinel2 : BAND_BY_SCALE
```

### Server Method Responsibilities

| Method | GEE Primitive |
|--------|---------------|
| `correct()` / `l1_to_l2()` | Orchestration — calls `l1_to_rrs` then per-image DSF loop |
| `compute_pdark()` | `reduceRegion(Reducer.percentile)` → **`getInfo()`** bridge |
| `compute_rhos()` | `image.expression()` — applies correction formula per band |
| `deglint_alternative()` | `image.subtract()` + `updateMask()` |
| `non_water()` / `cirrus_mask()` / `toa_mask()` | `B11.lt()` / `B10.lt()` / `band.lt()` |
| `add_cld_shdw_mask()` | `directionalDistanceTransform()`, `focal_min/max()` |
| `spm_nechad2016*` / `tur_nechad2016*` | `image.expression('A*R/(1-R/C)')` |
| `chl_oc2()` / `chl_oc3()` | `image.log()` + polynomial expression |
| `rrs()` | `image.divide(math.pi)` |
| `multi_image()` | `qualityMosaic(band)` |

---

## Client ↔ Server Communication

There are exactly **two points** where the client blocks waiting for GEE to return data:

```mermaid
sequenceDiagram
    participant Client as Local Python
    participant GEE as GEE Server

    Note over Client: DSF loop — per image

    Client->>GEE: compute_pdark()<br/>reduceRegion(percentile or min)
    GEE-->>Client: .getInfo() → dark spectrum<br/>{ B1: 0.032, B2: 0.028, … }<br/>~13 floats, < 1 KB

    Note over Client: AOT estimation (numpy)<br/>Model selection (scipy)<br/>Extract atmospheric params

    Client->>GEE: compute_rhos(atm_params)<br/>image.expression(correction_formula)<br/>→ lazy ee.Image (no blocking)

    Note over Client,GEE: ─── Bathymetry only ───

    Client->>GEE: calibrate_sdb()<br/>sampleRegions() + Reducer.linearFit()
    GEE-->>Client: .getInfo() → { slope, offset }<br/>2 floats
```

!!! warning "Performance note"
    `getInfo()` is called **once per image** in `compute_pdark()`. All other GEE operations are lazy and batched. Processing time scales **linearly with the number of images**.

### Data transferred at each bridge point

| Call | Direction | Payload | Blocking |
|------|-----------|---------|----------|
| `compute_pdark().getInfo()` | GEE → Client | 13 floats (dark spectrum) | Yes, per image |
| `calibrate_sdb().getInfo()` | GEE → Client | 2 floats (slope, offset) | Yes, once |
| `compute_rhos(atm_params)` | Client → GEE | 4 floats per band × 13 bands | No (lazy) |

---

## Module Dependency Graph

```mermaid
graph TD
    PKG[gee_acolite]
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

---

## Water Quality — PRODUCTS Registry

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
    P --> L["Rrs_B1 … Rrs_B12"]
```

---

## Masking Pipeline

```mermaid
flowchart TD
    A[compute_water_mask] --> B[non_water<br/>B11 &lt; threshold]
    A --> C[cirrus_mask<br/>B10 &lt; threshold]
    A --> D[toa_mask<br/>band &lt; threshold]
    A --> E[add_cld_shdw_mask<br/>optional]
    B --> F[Combined mask — updateMask]
    C --> F
    D --> F
    E --> F

    style A fill:#e1f5ff
    style F fill:#e1ffe1
```

---

## Sentinel-2 Band Configuration

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
