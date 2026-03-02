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

### Version 0.1.0 (2024)

- Initial implementation
- Support for Sentinel-2
- DSF atmospheric correction
- Basic water quality parameters

### Roadmap

**v0.2.0** (Planned)
- Support for Landsat 8/9
- Tiled mode for AOT
- More bathymetry algorithms

**v0.3.0** (Future)
- Optimized temporal processing
- Export to cloud-optimized formats
- Interactive dashboard

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

**Sergio** - Development and implementation

### Contributors

- See [Contributors](https://github.com/Aouei/gee_acolite/graphs/contributors)

### Acknowledgments

- **Dr. Quinten Vanhellemont** - ACOLITE development
- **GEE Community** - Tools and support
- **Users and testers** - Feedback and bug reports

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
@software{gee_acolite2024,
  title = {GEE ACOLITE: Atmospheric correction for Google Earth Engine},
  author = {Sergio},
  year = {2024},
  url = {https://github.com/Aouei/gee_acolite},
  version = {0.1.0}
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
- **Email**: [Project contact]

## Links

### Project

- [GitHub Repository](https://github.com/Aouei/gee_acolite)
- [Documentation](https://aouei.github.io/gee_acolite/)
- [PyPI](https://pypi.org/project/gee-acolite/) _(coming soon)_

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
