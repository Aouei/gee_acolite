[![DOI](https://zenodo.org/badge/961844693.svg)](https://doi.org/10.5281/zenodo.18367865)
[![PyPI version](https://img.shields.io/pypi/v/gee_acolite.svg)](https://pypi.org/project/gee_acolite/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue.svg)](https://www.python.org/)

# GEE ACOLITE

Atmospheric correction for Sentinel-2 imagery on Google Earth Engine using the ACOLITE Dark Spectrum Fitting (DSF) method.

## Description

`gee_acolite` adapts the [ACOLITE](https://github.com/acolite/acolite) atmospheric correction to Google Earth Engine workflows. A single global AOT is estimated per image using ACOLITE LUTs (client-side), while all pixel operations run server-side on GEE.

**Key features:**

- **Dark Spectrum Fitting**: darkest pixel, percentile, or intercept methods
- **AOT Estimation**: single fixed AOT per image via LUT interpolation
- **Atmospheric Correction**: full LUT-based surface reflectance retrieval
- **Water Quality Products**: SPM, turbidity, chlorophyll-a, Rrs, bathymetry indices
- **Cloud & Water Masking**: integration with Sentinel-2 Cloud Probability

## Installation

```bash
pip install gee_acolite
```

### ACOLITE

`gee_acolite` requires ACOLITE for LUT loading and atmospheric calculations. ACOLITE is not on PyPI — download it from its [official repository](https://github.com/acolite/acolite) and add it to your Python path:

```python
import sys
sys.path.append('/path/to/acolite')

import acolite as ac
from gee_acolite import ACOLITE
```

## Quickstart

```python
import sys
sys.path.append('/path/to/acolite')

import ee
import acolite as ac
from gee_acolite import ACOLITE
from gee_acolite.utils.search import search

ee.Initialize(project='your-cloud-project-id')

roi = ee.Geometry.Rectangle([-0.40, 39.27, -0.28, 39.38])
images = search(roi, '2023-06-01', '2023-06-30', tile='30SYJ')

settings = {
    's2_target_res': 10,
    'dsf_spectrum_option': 'darkest',
    'l2w_parameters': ['spm_nechad2016', 'chl_oc3', 'pSDB_green'],
}

ac_gee = ACOLITE(ac, settings)
corrected, final_settings = ac_gee.correct(images)
```

## Requirements

- Python ≥ 3.11
- `earthengine-api` ≥ 0.1.350
- `numpy` ≥ 1.20.0
- `scipy` ≥ 1.7.0
- `netcdf4` ≥ 1.7.0
- [ACOLITE](https://github.com/acolite/acolite) (separate installation)

## Documentation

Full documentation including API reference, examples, and architecture diagrams is available at:
**[https://aouei.github.io/gee_acolite](https://aouei.github.io/gee_acolite)**

## Water Quality Products

| Product | Description |
|---------|-------------|
| `spm_nechad2016` | Suspended particulate matter — 665 nm (Nechad 2016) |
| `spm_nechad2016_704` | SPM — 704 nm |
| `spm_nechad2016_740` | SPM — 740 nm |
| `tur_nechad2016` | Turbidity — 665 nm (Nechad 2016) |
| `chl_oc2` | Chlorophyll-a OC2 |
| `chl_oc3` | Chlorophyll-a OC3 |
| `chl_re_mishra` | Chlorophyll-a NDCI (Mishra) |
| `pSDB_green` | Pseudo satellite-derived bathymetry — green |
| `pSDB_red` | Pseudo satellite-derived bathymetry — red |
| `Rrs_B*` | Remote sensing reflectance (all 13 bands) |

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request.

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE) for details.

## Citation

If you use this package in your research, please cite:

```bibtex
@software{heredia_sergio_2026_gee_acolite,
  author    = {Heredia, Sergio},
  title     = {gee\_acolite},
  year      = {2026},
  version   = {1.0.1},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.18367865},
  url       = {https://doi.org/10.5281/zenodo.18367865}
}
```

And the original ACOLITE paper:

```bibtex
@article{vanhellemont2019,
  author  = {Vanhellemont, Quinten and Ruddick, Kevin},
  title   = {Adaptation of the dark spectrum fitting atmospheric correction for aquatic applications of the Landsat and Sentinel-2 archives},
  journal = {Remote Sensing of Environment},
  volume  = {225},
  pages   = {175--192},
  year    = {2019},
  doi     = {10.1016/j.rse.2019.03.010}
}
```

## Acknowledgments

This package is based on the ACOLITE software developed by RBINS (Royal Belgian Institute of Natural Sciences).

This software was developed at the [Institute of Marine Sciences of Andalusia (ICMAN-CSIC)](https://www.icman.csic.es/), Spanish National Research Council (CSIC), Puerto Real, Spain.

## Contact

- GitHub: [@Aouei](https://github.com/Aouei)
- Email: sergiohercar1@gmail.com
