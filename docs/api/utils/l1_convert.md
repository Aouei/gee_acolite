# L1 Conversion

Utilities for converting Sentinel-2 L1C Digital Numbers (DN) to TOA (Top-of-Atmosphere) reflectance, extracting viewing geometry, and resampling bands to a uniform resolution.

## Overview

The `gee_acolite.utils.l1_convert` module:

- Converts DN values to TOA reflectance (`DN / 10000`)
- Extracts solar and sensor viewing angles from image metadata
- Computes the relative azimuth angle (RAA)
- Resamples all bands to a common target resolution

## Conversion Flow

```mermaid
flowchart TD
    A["S2 L1C Image<br/>DN values"] --> B[DN_to_rrs]
    B --> C["Divide by 10000<br/>TOA reflectance 0-1"]
    C --> D[Extract Angles]
    D --> D1[Solar Zenith SZA]
    D --> D2[Solar Azimuth SAA]
    D --> D3["View Zenith VZA<br/>mean over 13 bands"]
    D --> D4["View Azimuth VAA<br/>mean over 13 bands"]
    D1 --> E["Compute RAA<br/>abs(SAA - VAA), clamped 0-180"]
    D2 --> E
    D4 --> E
    E --> F["Add geometry bands<br/>sza, saa, vza, vaa, raa"]
    F --> G["resample<br/>bilinear to target scale"]
    G --> H[TOA Image + Geometry]

    style A fill:#e1f5ff
    style H fill:#e1ffe1
    style E fill:#fef3c7
```

## Functions

::: gee_acolite.utils.l1_convert.l1_to_rrs
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: gee_acolite.utils.l1_convert.DN_to_rrs
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: gee_acolite.utils.l1_convert.resample
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

## Viewing Geometry

The geometry angles are critical inputs to the ACOLITE LUT interpolation:

```mermaid
graph TD
    A[Viewing Geometry] --> B[Solar Angles]
    A --> C[Sensor Angles]
    A --> D[Relative Angle]

    B --> B1[Solar Zenith SZA]
    B --> B2[Solar Azimuth SAA]

    C --> C1[View Zenith VZA]
    C --> C2[View Azimuth VAA]

    D --> D1["RAA = |SAA - VAA|, clamped to [0°, 180°]"]

    style D1 fill:#fef3c7
```

### Extracted Angles

| Angle | Output band | Source metadata property | Range |
|-------|-------------|--------------------------|-------|
| Solar Zenith (SZA) | `sza` | `MEAN_SOLAR_ZENITH_ANGLE` | 0°–90° |
| Solar Azimuth (SAA) | `saa` | `MEAN_SOLAR_AZIMUTH_ANGLE` | 0°–360° |
| View Zenith (VZA) | `vza` | Mean of `MEAN_INCIDENCE_ZENITH_ANGLE_B*` (13 bands) | 0°–90° |
| View Azimuth (VAA) | `vaa` | Mean of `MEAN_INCIDENCE_AZIMUTH_ANGLE_B*` (13 bands) | 0°–360° |
| Relative Azimuth (RAA) | `raa` | `|SAA - VAA|`, clamped to [0°, 180°] | 0°–180° |

## Spatial Resolutions

Sentinel-2 MSI has three native resolutions. All bands are resampled to a single target resolution using the reference band for that scale:

```mermaid
graph LR
    A[S2 Bands] --> B[10m]
    A --> C[20m]
    A --> D[60m]

    B --> B1["B2, B3, B4, B8\nReference: B2"]
    C --> C1["B5, B6, B7, B8A, B11, B12\nReference: B5"]
    D --> D1["B1, B9, B10\nReference: B1"]

    style B fill:#dcfce7
    style C fill:#fef3c7
    style D fill:#dbeafe
```

### Full Band Table

| Band | Name | Central λ (nm) | Width (nm) | Native res. | Use |
|------|------|----------------|------------|------------|-----|
| B1 | Coastal Aerosol | 443 | 21 | 60m | Aerosol correction |
| B2 | Blue | 492 | 66 | 10m | Ocean, bathymetry |
| B3 | Green | 560 | 36 | 10m | Water quality |
| B4 | Red | 665 | 31 | 10m | SPM, turbidity |
| B5 | Red Edge 1 | 705 | 15 | 20m | Chlorophyll |
| B6 | Red Edge 2 | 740 | 15 | 20m | Vegetation |
| B7 | Red Edge 3 | 783 | 20 | 20m | Vegetation |
| B8 | NIR | 842 | 106 | 10m | Water mask, shadows |
| B8A | Narrow NIR | 865 | 21 | 20m | Water vapour |
| B9 | Water Vapour | 945 | 20 | 60m | Atmospheric correction |
| B10 | Cirrus | 1375 | 31 | 60m | Cirrus detection |
| B11 | SWIR 1 | 1610 | 91 | 20m | Water/land mask, glint |
| B12 | SWIR 2 | 2190 | 175 | 20m | Glint reference |

## Usage Examples

### Full Collection Conversion

```python
import ee
from gee_acolite.utils.search import search
from gee_acolite.utils.l1_convert import l1_to_rrs

ee.Initialize(project='your-project-id')

roi = ee.Geometry.Rectangle([-0.5, 39.3, -0.1, 39.7])
images_l1c = search(roi, '2023-06-15', '2023-06-16', tile='30SYJ')

# Convert to TOA reflectance at 10m
images_toa = l1_to_rrs(images_l1c, scale=10)

# Inspect output bands
band_names = images_toa.first().bandNames().getInfo()
print(band_names)
# ['B1', 'B2', ..., 'B12', 'sza', 'saa', 'vza', 'vaa', 'raa']
```

### Single Image Conversion

```python
from gee_acolite.utils.l1_convert import DN_to_rrs

image_toa = DN_to_rrs(images_l1c.first())

# Access geometry
sza_mean = image_toa.select('sza').reduceRegion(
    ee.Reducer.mean(), roi, 1000
).getInfo()
print(f'Mean SZA: {sza_mean}')
```

## DN to Reflectance Formula

The conversion for Sentinel-2 L1C is:

$$
\rho_{\text{TOA}} = \frac{DN}{10000}
$$

This normalises all band values to the range [0, 1], which is required by the ACOLITE LUT interpolation.

## RAA Computation

The relative azimuth angle is computed from solar and sensor azimuths and clamped to [0°, 180°] to match the LUT indexing:

$$
\text{RAA} = |\phi_s - \phi_v|, \quad \text{if RAA} > 180° \Rightarrow \text{RAA} = 360° - \text{RAA}
$$

## Integration with ACOLITE

```mermaid
sequenceDiagram
    participant GEE
    participant L1Convert
    participant ACOLITE_LUT as ACOLITE LUTs

    GEE->>L1Convert: ImageCollection L1C (DN)
    L1Convert->>L1Convert: DN / 10000
    L1Convert->>L1Convert: Extract angles (SZA, SAA, VZA, VAA, RAA)
    L1Convert->>L1Convert: Bilinear resample to target scale
    L1Convert->>ACOLITE_LUT: TOA + geometry → LUT lookup (SZA, VZA, RAA, tau)
    ACOLITE_LUT->>ACOLITE_LUT: Interpolate atmospheric parameters
    ACOLITE_LUT->>GEE: romix, dutott, astot, tg per band
```

## References

- [Sentinel-2 L1C Product Specification (ESA)](https://sentinel.esa.int/documents/247904/349490/S2_MSI_Product_Specification.pdf)
- [GEE COPERNICUS/S2_HARMONIZED Dataset](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_HARMONIZED)
