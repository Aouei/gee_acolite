# gee_acolite Documentation

📚 **The full documentation is available at: https://aouei.github.io/gee_acolite/**

## Documentation Overview

This folder contains documentation files for the gee_acolite project:

- [API Reference](API.md) - Complete API documentation
- **Sphinx Documentation** - Modern, comprehensive documentation at https://aouei.github.io/gee_acolite/

## Building Sphinx Documentation Locally

### Prerequisites

```bash
pip install sphinx sphinx-book-theme nbsphinx ipython
```

### Build

**Windows:**
```bash
cd ../sphinx
.\make.bat html
```

**Linux/Mac:**
```bash
cd ../sphinx
make html
```

The generated documentation will be in `../sphinx/build/html/index.html`.

## Quick Links

- **GitHub Repository:** https://github.com/Aouei/gee_acolite
- **Online Documentation:** https://aouei.github.io/gee_acolite/
- **Examples:** [../examples/](../examples/)
- **Issues:** https://github.com/Aouei/gee_acolite/issues

## Getting Started

1. Visit the [Installation Guide](https://aouei.github.io/gee_acolite/user_guide/installation.html)
2. Follow the [Quick Start](https://aouei.github.io/gee_acolite/user_guide/quickstart.html)
3. Check out [Examples](https://aouei.github.io/gee_acolite/examples/basic_usage.html)
4. Explore the [API Reference](https://aouei.github.io/gee_acolite/modules/correction.html)

## Contributing to Documentation

1. Edit the `.rst` files in `../sphinx/source/`
2. Build locally to preview changes
3. Commit and push to the `docs` branch
4. GitHub Actions will automatically deploy to GitHub Pages

## Support

- Open an [issue](https://github.com/Aouei/gee_acolite/issues) for bugs
- Check [examples](../examples/) for common use cases
- Read the [online documentation](https://aouei.github.io/gee_acolite/)
