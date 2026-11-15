# About GEE ACOLITE

## Project Description

GEE ACOLITE is an adaptation of the ACOLITE software (Atmospheric Correction for Aquatic Applications of satellites for Identifying and Tracking Ecosystems) optimized to work with Google Earth Engine (GEE) and Sentinel-2 imagery.

The project combines:

- **ACOLITE**: State-of-the-art atmospheric correction algorithms
- **Google Earth Engine**: Scalable cloud processing
- **Python**: Flexible programmatic interface

## Motivation

### Problem

Atmospheric correction of satellite images for aquatic applications is complex:

- Standard algorithms (Sen2Cor, LaSRC) are designed for land
- Local processing of large areas is computationally expensive
- Integrating multiple tools is complicated

### Solution

GEE ACOLITE offers:

✅ Specialized atmospheric correction for water  
✅ Scalable processing in GEE  
✅ Simple and consistent Python interface  
✅ Integration with the scientific Python ecosystem

## History

### Version 1.0.1

- Initial public release on PyPI
- Support for Sentinel-2
- DSF atmospheric correction via ACOLITE
- Water quality parameters (SPM, turbidity, Chl-a, Rrs)

### Version 1.2.0

- Bathymetry improvements: pSDB median filter
- Bathymetry calibration enhancements (`calibrate_sdb`, `apply_calibration`, `multi_image`)
- ICMAN attribution

### Version 1.2.1

- Support for ACOLITE 2025.01 and 2026.04, in addition to 2023.10 (settings defaults are now merged explicitly)
- The atmospheric correction algorithm setting (`aerosol_correction` and its renamed successors) is ignored; only fixed DSF is run
- Documentation of ACOLITE version compatibility

### Unreleased

- ACOLITE parity of the fixed dark spectrum fitting (same AOT and aerosol model as ACOLITE 20231023 for the same L1 image):
    - `s2_resampling_method` (new, default `'nearest'`): 20 m / 60 m bands are replicated, not bilinearly interpolated, when brought to the target grid. Use `'bilinear'` for the previous behaviour
    - `dsf_spectrum_option='darkest'` now uses the true minimum over all valid pixels instead of a `bestEffort` subsample
    - `dsf_allow_lut_boundaries` (new, default `False`): bands whose dark spectrum falls outside the LUT range get a NaN AOT and are ignored, instead of being clamped to the lowest LUT AOT. If no band is valid the AOT is 0.01, as in ACOLITE
    - `dsf_aot_compute` (new, default `'min'`): the AOT is that of the lowest band, as in ACOLITE; `'mean'` and `'median'` are available
- **Bug fix, residual sun glint correction**: the glint ratios (sky reflectance of each band relative to B11/B12) were evaluated at the selected AOT. The sky-reflectance LUT is exactly 0 in B11/B12 for AOT <= 0.05, so in 1.2.x (and earlier) the ratio was infinite and `dsf_residual_glint_correction` silently removed **no glint** for those scenes, while for AOT in (0.05, 0.1) it removed too much. The ratios are now evaluated at `max(glint_aot_floor, AOT)` with `glint_aot_floor=0.1` (ACOLITE 20231023 behaviour); the atmospheric correction keeps the real AOT. Setting `glint_aot_floor` to `0` restores the previous behaviour. If the SWIR reference is not finite and positive the glint correction is skipped with a warning. With the same L1 image, AOT and aerosol model, surface reflectance now matches ACOLITE 20231023 (validated on 15 images of three study sites with the same L1 baseline: median bias and RMSE below 1e-5 sr^-1, worst image 7e-5 sr^-1)
- **Behaviour change**: the defaults differ from 1.2.x (the version used for the published paper), so AOT, aerosol model and surface reflectance can change for the same input. See *Configuration* for the settings that restore the previous behaviour

## Main Components

### ACOLITE Core

Developed by Dr. Quinten Vanhellemont (RBINS):

- Dark Spectrum Fitting (DSF) for AOT
- Pre-calculated LUTs with OSOAA/6S
- Atmospheric gas correction
- Aquatic product algorithms

**Citation:**
```
Vanhellemont, Q., & Ruddick, K. (2018). Atmospheric correction of 
metre-scale optical satellite data for inland and coastal water
applications. Remote Sensing of Environment, 216, 586-597.
```

### Google Earth Engine

Google's platform for geospatial analysis:

- Petabyte-scale data catalog
- Distributed cloud processing
- Python and JavaScript API

### Python Scientific Stack

- **NumPy/SciPy**: Numerical calculations
- **Pandas**: Data manipulation
- **Matplotlib**: Visualizations
- **geemap**: Interactive GEE interface

## Use Cases

### Scientific Research

- Water quality monitoring
- Eutrophication studies
- Sediment dynamics
- Benthic habitat mapping

### Environmental Management

- Algal bloom monitoring
- Turbidity tracking
- Impact assessment
- Coastal planning

### Education

- Remote sensing teaching
- Student projects
- Workshops and courses

## Team

### Lead Developer

**[Sergio (Aouei)](https://github.com/Aouei)** - Development and implementation

### Contributors

- See [Contributors](https://github.com/Aouei/gee_acolite/graphs/contributors)

### Acknowledgments

- **Dr. Quinten Vanhellemont** - ACOLITE development
- **GEE Community** - Tools and support

## License

GEE ACOLITE is licensed under GPL-3.0, same as ACOLITE.

```
Copyright (C) 2024 Sergio

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
```

See [LICENSE](https://github.com/Aouei/gee_acolite/blob/main/LICENSE) for details.

## Dependencies

### Main

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| ACOLITE | >=2023.6 | GPL-3.0 | Atmospheric correction |
| earthengine-api | >=0.1.300 | Apache-2.0 | GEE interface |
| numpy | >=1.20 | BSD | Numerical calculations |
| scipy | >=1.7 | BSD | Interpolation |

### Optional

| Package | Purpose |
|---------|---------|
| geemap | Interactive visualization |
| matplotlib | Plots |
| pandas | Data analysis |

## Citation

If you use GEE ACOLITE in your research, please cite:

```bibtex
@software{gee_acolite2026,
  title = {GEE ACOLITE: Atmospheric correction for Google Earth Engine},
  author = {Sergio},
  year = {2026},
  url = {https://github.com/Aouei/gee_acolite},
  version = {1.0.1}
}
```

And also ACOLITE:

```bibtex
@article{vanhellemont2018atmospheric,
  title={Atmospheric correction of metre-scale optical satellite data 
         for inland and coastal water applications},
  author={Vanhellemont, Q and Ruddick, K},
  journal={Remote Sensing of Environment},
  volume={216},
  pages={586--597},
  year={2018},
  publisher={Elsevier}
}
```

## Contact

- **Issues**: [GitHub Issues](https://github.com/Aouei/gee_acolite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Aouei/gee_acolite/discussions)

## Links

### Project

- [GitHub Repository](https://github.com/Aouei/gee_acolite)
- [Documentation](https://aouei.github.io/gee_acolite/)
- [PyPI](https://pypi.org/project/gee-acolite/)

### Related Resources

- [ACOLITE GitHub](https://github.com/acolite/acolite)
- [Google Earth Engine](https://earthengine.google.com/)
- [Sentinel-2](https://sentinel.esa.int/web/sentinel/missions/sentinel-2)
- [geemap](https://geemap.org/)

### Related Publications

- Vanhellemont, Q. (2019). Adaptation of the dark spectrum fitting atmospheric correction for aquatic applications of the Landsat and Sentinel-2 archives. Remote Sensing of Environment, 225, 175-192.
- Vanhellemont, Q., & Ruddick, K. (2018). Atmospheric correction of metre-scale optical satellite data for inland and coastal water applications. Remote Sensing of Environment, 216, 586-597.
- Gorelick, N., et al. (2017). Google Earth Engine: Planetary-scale geospatial analysis for everyone. Remote Sensing of Environment, 202, 18-27.

## Project Status

### Stability

- ⚠️ **Beta**: API may change
- ✅ **Functional**: Main use cases work
- 🚧 **Actively developed**: Continuous improvements

### Metrics

![GitHub stars](https://img.shields.io/github/stars/Aouei/gee_acolite)
![GitHub forks](https://img.shields.io/github/forks/Aouei/gee_acolite)
![GitHub issues](https://img.shields.io/github/issues/Aouei/gee_acolite)
![GitHub license](https://img.shields.io/github/license/Aouei/gee_acolite)

### Contributing

Contributions are welcome! See [Contribution Guide](contributing.md).

## Acknowledgments

This project would not be possible without:

- 🎓 **Scientific community** of aquatic remote sensing
- 🌍 **ESA/Copernicus** for open Sentinel-2 data
- 🔬 **RBINS** and Dr. Vanhellemont for ACOLITE
- ☁️ **Google** for Earth Engine
- 🐍 **Python community** and scientific library developers

---

**GEE ACOLITE** - Making aquatic atmospheric correction accessible and scalable.

> This software was developed at the Institute of Marine Sciences of Andalusia (ICMAN-CSIC),
> Spanish National Research Council (CSIC), Puerto Real, Spain.
