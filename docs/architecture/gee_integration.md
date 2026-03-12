# GEE Integration

How GEE ACOLITE integrates with Google Earth Engine — what runs on the server, what runs on the client, and why.

---

## Architecture Overview

GEE ACOLITE uses a **hybrid processing model** that combines:

- **Client-side (local Python):** ACOLITE LUT loading, AOT estimation, model selection
- **Server-side (GEE cloud):** All image operations, band arithmetic, masking, product computation

This design is necessary because ACOLITE's atmospheric correction requires LUT interpolation that cannot be expressed as a GEE computation graph, while pixel-level image operations benefit from GEE's massive parallelism.

```mermaid
graph TB
    subgraph Client["Client — Local Python Process"]
        Script["User Script"]
        GEE_ACO["gee_acolite\nACOLITE class"]
        ACOLITE_PKG["ACOLITE package\n(LUTs, gas_transmittance,\nancillary data)"]
        NUMPY["numpy / scipy\n(AOT estimation,\nmodel selection)"]
        EE_CLIENT["earthengine-api\n(Python bindings)"]
    end

    subgraph GEE["Server — Google Earth Engine Cloud"]
        GEE_API["Earth Engine API\n(REST / gRPC)"]
        S2_CAT["Sentinel-2 Catalog\nCOPERNICUS/S2_HARMONIZED"]
        COMPUTE["Cloud Compute\n(image expressions,\nreducers, masking)"]
        STORAGE["GEE Storage\n(Assets, Drive export)"]
    end

    Script --> GEE_ACO
    GEE_ACO --> ACOLITE_PKG
    GEE_ACO --> NUMPY
    GEE_ACO --> EE_CLIENT
    EE_CLIENT <-->|HTTPS requests| GEE_API
    GEE_API --> S2_CAT
    GEE_API --> COMPUTE
    COMPUTE --> STORAGE

    style Client fill:#dbeafe,stroke:#3b82f6
    style GEE fill:#dcfce7,stroke:#16a34a
```

---

## Client vs Server: Operation Classification

### Client-Side Operations

These run in the local Python process and **block until complete**:

```mermaid
sequenceDiagram
    participant User
    participant Python as Local Python
    participant AC as ACOLITE LUTs
    participant GEE as GEE Server

    User->>Python: ACOLITE(ac, settings)
    Python->>AC: parse settings → S2A_MSI defaults
    Python->>AC: import_luts() — load LUT files from disk

    loop For each image
        Python->>GEE: compute_pdark() — reduceRegion()
        GEE-->>Python: getInfo() → dark spectrum dict
        Note over Python,AC: ← Only network call that blocks per image

        Python->>AC: LUT interpolation (np.interp)
        Python->>Python: estimate_aot_per_lut() — AOT per model
        Python->>Python: select_best_model() — pick best LUT + AOT

        Python->>GEE: compute_rhos() — submit lazy computation
        Note over GEE: Runs server-side, no blocking
    end
```

| Operation | Function | Why client-side |
|-----------|----------|-----------------|
| Settings parsing | `__load_settings()` | ACOLITE API, not expressible in GEE |
| LUT loading | `import_luts()`, `import_rsky_luts()` | NetCDF files on local disk |
| Gas transmittance | `gas_transmittance()` | ACOLITE spectral model |
| Dark spectrum retrieval | `compute_pdark() → .getInfo()` | Must be a scalar to feed into LUT |
| AOT estimation | `estimate_aot_per_lut()` | numpy LUT interpolation |
| Model selection | `select_best_model()` | numpy/scipy statistics |
| Ancillary data | `get_ancillary_data()` | NASA Earthdata HTTP API |
| SDB calibration readout | `calibrate_sdb() → .getInfo()` | Regression coefficients needed locally |

### Server-Side Operations

These return `ee.Image` or `ee.ImageCollection` objects. They are **lazy** — no computation happens until `.getInfo()`, `.export()`, or tile rendering is triggered.

| Operation | Function | GEE primitive used |
|-----------|----------|--------------------|
| Image search | `search()` | `filterBounds`, `filterDate`, `filter` |
| DN → TOA | `DN_to_rrs()` | `image.divide(10000)` |
| Geometry angles | `get_mean_band_angle()` | `image.get()`, `ee.Number.parse()` |
| Resampling | `resample()` | `resample('bilinear')`, `reproject()` |
| Dark spectrum (send) | `compute_pdark()` | `reduceRegion(Reducer.percentile)` |
| Surface reflectance | `compute_rhos()` | `image.expression(correction_formula)` |
| Negative mask | `mask_negative_reflectance()` | `updateMask(image.gte(0))` |
| Water/land mask | `non_water()` | `B11.lt(threshold)` |
| Cirrus mask | `cirrus_mask()` | `B10.lt(threshold)` |
| Cloud mask | `toa_mask()` | `band.lt(threshold)` |
| Shadow detection | `add_shadow_bands()` | `directionalDistanceTransform()` |
| Shadow mask | `add_cld_shdw_mask()` | `focal_min()`, `focal_max()` |
| Glint correction | `deglint_alternative()` | `image.subtract()`, `updateMask()` |
| SPM / Turbidity | `spm_nechad2016*`, `tur_nechad2016*` | `image.expression()` |
| Chlorophyll OC2/OC3 | `chl_oc2()`, `chl_oc3()` | `image.log()`, polynomial expression |
| Chlorophyll NDCI | `chl_re_mishra()` | `normalizedDifference(['B5','B4'])` |
| pSDB | `pSDB_green()`, `pSDB_red()` | `image.log()` arithmetic |
| Rrs | `rrs()` | `image.divide(math.pi)` |
| Bathymetry mosaic | `multi_image()` | `qualityMosaic(band)` |
| SDB calibration (fit) | `calibrate_sdb()` | `sampleRegions()`, `Reducer.linearFit()` |
| SDB apply | `apply_calibration()` | `image.multiply(slope).add(intercept)` |

---

## GEE Lazy Evaluation

GEE uses **deferred execution**: Python code builds a computation graph but nothing runs until explicitly requested.

```mermaid
sequenceDiagram
    participant Code as Python Code
    participant API as GEE Python API (local)
    participant Server as GEE Server

    Note over Code,API: Graph construction (instant, local)
    Code->>API: image = search(roi, start, end)
    Code->>API: toa = l1_to_rrs(image, scale=10)
    Code->>API: rhos = compute_rhos(toa, am)
    Code->>API: spm = spm_nechad2016_665(rhos)

    Note over Code,Server: Execution triggered by .getInfo() or export
    Code->>API: spm.reduceRegion(...).getInfo()
    API->>Server: Execute full pipeline
    Server-->>API: Computed values
    API-->>Code: Python dict
```

**Consequence for gee_acolite:** the correction formula `compute_rhos()` is never actually executed on any pixel during Python execution — only when the result is exported or `.getInfo()` is called by the user.

---

## The getInfo() Bottleneck

The single `getInfo()` per image in `compute_pdark()` is unavoidable but minimised:

```python
# Inside compute_pdark() — the only blocking call per image
pdark = image.reduceRegion(
    reducer=reducer,          # percentile or min
    geometry=image.geometry(),
    scale=settings.get('s2_target_res', 10),
    maxPixels=1e9,
).getInfo()  # ← transfers ~13 float values from GEE to Python
```

The response is a dict of 13 scalar values (one per band), typically < 1 KB. Everything else (the correction, the products, the masking) runs server-side without blocking.

```mermaid
flowchart LR
    A["N images"] --> B["N × getInfo()\nDark spectrum only"]
    B --> C["Local AOT estimation\n~milliseconds each"]
    C --> D["Server-side correction\n(lazy, no blocking)"]
    D --> E["Export / getInfo\non final result"]
```

---

## Export to GeoTIFF

After correction, results live in GEE as lazy `ee.Image` / `ee.ImageCollection` objects. To work with them locally as GeoTIFFs, use [geemap](https://geemap.org).

### Dependencies

```python
import geemap
from datetime import datetime, timedelta
from gee_acolite import ACOLITE
from gee_acolite.utils.search import search_list
from gee_acolite import bathymetry
```

### Download a single mosaic

Use `bathymetry.multi_image()` to collapse a corrected collection into a quality mosaic, then download it as a single GeoTIFF.

```python
bands = [
    'Rrs_B1', 'Rrs_B2', 'Rrs_B3', 'Rrs_B4',
    'Rrs_B5', 'Rrs_B6', 'Rrs_B7', 'Rrs_B8', 'Rrs_B8A',
    'Rrs_B11', 'Rrs_B12',
    'pSDB_green', 'pSDB_red',
    'tur_nechad2016', 'chl_oc3',
]

roi    = ee.Geometry.Rectangle([...])
starts = ['2018-09-19', '2018-10-04', '2018-10-17']
ends   = [
    (datetime.strptime(d, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    for d in starts
]

corrector    = ACOLITE(acolite=acolite, settings='settings.txt')
collection   = search_list(roi, starts, ends, tile='29SND')
corrected, _ = corrector.correct(collection)

mosaic = bathymetry.multi_image(corrected)

geemap.download_ee_image(
    image=mosaic.select(bands),
    filename='output/mosaic.tif',
    region=roi,
    crs='EPSG:32629',
    scale=10,
    dtype='float32',
)
```

!!! tip "Masked pixels and NaN"
    GEE exports masked pixels as `nodata`. When opening the result with rasterio or xarray, use `masked=True` or set `nodata=float('nan')` to avoid treating them as valid zeros or infinities.

### Download an image collection (one file per scene)

```python
filenames = [f'{d.replace("-", "_")}.tif' for d in starts]

geemap.download_ee_image_collection(
    collection=corrected.select(bands),
    out_dir='output/scenes/',
    filenames=filenames,
    region=roi,
    crs='EPSG:32629',
    scale=10,
    dtype='float32',
)
```

### Choosing between the two

| Use case | Function |
|----------|----------|
| Single composite / best-pixel mosaic | `download_ee_image` + `multi_image()` |
| Time series / individual scenes | `download_ee_image_collection` |
| Large area or many scenes (async) | `ee.batch.Export.image.toDrive` |

---