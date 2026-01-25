[![DOI](https://zenodo.org/badge/961844693.svg)](https://doi.org/10.5281/zenodo.18367146)

# GEE ACOLITE

ACOLITE atmospheric correction implementation for Google Earth Engine (GEE).

## Description

This package provides atmospheric correction for Sentinel-2 imagery using the ACOLITE dark spectrum fitting method, optimized for Google Earth Engine workflows. It includes:

- **Dark Spectrum Fitting**: Multiple methods (darkest, percentile, intercept)
- **AOT Estimation**: Fixed geometry mode
- **Atmospheric Correction**: Full LUT-based correction
- **Water Quality Parameters**: SPM, turbidity, chlorophyll, bathymetry indices
- **Cloud Masking**: Integration with Sentinel-2 Cloud Probability

## Installation

### From PyPI (when published)

```bash
pip install gee_acolite
```

### From source

```bash
git clone https://github.com/Aouei/gee_acolite.git
cd gee_acolite
pip install -e .
```

## Features

### Atmospheric Correction Methods

- **Fixed Geometry**: Single AOT estimation for entire image
- **Dark Spectrum Options**:
  - `darkest`: Use minimum values
  - `percentile`: Use Nth percentile
  - `intercept`: Linear regression intercept

### Model Selection Criteria

- `min_drmsd`: Minimum RMSD between observed and modeled reflectance
- `min_dtau`: Minimum delta AOT between darkest bands
- `taua_cv`: Minimum coefficient of variation

### Water Quality Products

- **SPM**: Suspended particulate matter (Nechad 2016)
- **Turbidity**: Water turbidity (Nechad 2016)
- **Chlorophyll**: Chl-a concentration (OC2, OC3, Mishra)
- **Bathymetry**: Pseudo satellite-derived bathymetry (pSDB)
- **Indices**: NDWI, custom band ratios

## Requirements

- Python ≥ 3.8
- earthengine-api ≥ 0.1.350
- numpy ≥ 1.20.0
- scipy ≥ 1.7.0
- **ACOLITE** (standalone installation required)

### Installing ACOLITE

This package requires the ACOLITE atmospheric correction software to be installed separately:

```bash
# Clone ACOLITE repository
git clone https://github.com/acolite/acolite.git

# Install ACOLITE
cd acolite
pip install -e .
```

**Important:** ACOLITE is not available on PyPI and must be installed from source.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this package in your research, please cite:

```bibtex
@software{gee_acolite,
  author = {Sergio},
  title = {GEE ACOLITE: Atmospheric Correction for Google Earth Engine},
  year = {2025},
  url = {https://github.com/Aouei/gee_acolite}
}
```

And the original ACOLITE paper:

```bibtex
@article{vanhellemont2019,
  title={Adaptation of the dark spectrum fitting atmospheric correction for aquatic applications of the Landsat and Sentinel-2 archives},
  author={Vanhellemont, Quinten and Ruddick, Kevin},
  journal={Remote Sensing of Environment},
  volume={225},
  pages={175--192},
  year={2019},
  publisher={Elsevier}
}
```

## Acknowledgments

This package is based on the ACOLITE software developed by RBINS (Royal Belgian Institute of Natural Sciences).

## Contact

- GitHub: [@Aouei](https://github.com/Aouei)
- Email: sergiohercar1@gmail.com
