# Contributing

Guide for contributing to the GEE ACOLITE project.

## Ways to Contribute

### 🐛 Report Bugs

If you find a bug:

1. Check that it hasn't already been reported in [Issues](https://github.com/Aouei/gee_acolite/issues)
2. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs. observed behavior
   - Python, GEE, ACOLITE version
   - Minimal reproducible code

**Issue Template:**

```markdown
### Bug Description
[Clear and concise description]

### Steps to Reproduce
1. ...
2. ...
3. ...

### Expected Behavior
[What you expected to happen]

### Actual Behavior
[What actually happened]

### Environment
- OS: [e.g., Ubuntu 20.04, Windows 11]
- Python: [e.g., 3.10.0]
- gee_acolite: [e.g., 0.1.0]
- ACOLITE: [e.g., 20230607.0]
- earthengine-api: [e.g., 0.1.370]

### Reproducible Code
```python
# Minimal code to reproduce the error
```

### Traceback
```
[Paste the full traceback here]
```
```

### ✨ Request Features

For new features:

1. Describe the use case
2. Explain why it is useful
3. Provide examples of how it would be used

### 📝 Improve Documentation

- Fix typos
- Clarify explanations
- Add examples
- Translate to other languages

### 💻 Contribute Code

See the [Development](#development) section below.

## Development

### Setting Up the Development Environment

```bash
# Fork and clone
git clone https://github.com/your-username/gee_acolite.git
cd gee_acolite
git submodule update --init --recursive

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Project Structure

```
gee_acolite/
├── gee_acolite/          # Source code
│   ├── __init__.py
│   ├── correction.py     # Atmospheric correction
│   ├── water_quality.py  # Water parameters
│   ├── bathymetry.py     # Bathymetry
│   ├── utils/            # Utilities
│   └── sensors/          # Sensor configs
├── tests/                # Tests
│   ├── test_correction.py
│   ├── test_water_quality.py
│   └── test_utils.py
├── docs/                 # Documentation
├── examples/             # Example notebooks
├── pyproject.toml        # Package config
└── README.md
```

### Code Style

We follow [PEP 8](https://pep8.org/) with some conventions:

```python
# Ordered imports
import os
import sys

import numpy as np
import pandas as pd

import ee

from gee_acolite.utils import masks

# NumPy-style docstrings
def function_name(param1, param2):
    """
    One-line brief description.
    
    More detailed description if needed.
    
    Parameters
    ----------
    param1 : type
        Description of parameter 1
    param2 : type
        Description of parameter 2
        
    Returns
    -------
    type
        Description of return value
        
    Examples
    --------
    >>> function_name(1, 2)
    3
    """
    return param1 + param2

# Type hints when possible
from typing import Optional, List, Tuple

def search(
    roi: ee.Geometry,
    start: str,
    end: str,
    tile: Optional[str] = None
) -> ee.ImageCollection:
    """..."""
    pass
```

### Testing

We use `pytest` for testing:

```bash
# Run all tests
pytest

# With coverage
pytest --cov=gee_acolite --cov-report=html

# Specific test
pytest tests/test_correction.py::test_acolite_init
```

**Writing Tests:**

```python
# tests/test_water_quality.py

import pytest
import ee
from gee_acolite.water_quality import compute_water_mask

@pytest.fixture
def sample_image():
    """Fixture for test image"""
    ee.Initialize()
    return ee.Image('COPERNICUS/S2_HARMONIZED/20230615T103031_20230615T103026_T30SYJ')

def test_compute_water_mask(sample_image):
    """Test water mask"""
    settings = {'l2w_mask_threshold': 0.05}
    mask = compute_water_mask(sample_image, settings)
    
    assert isinstance(mask, ee.Image)
    assert 'water_mask' in mask.bandNames().getInfo()

def test_invalid_threshold():
    """Test threshold validation"""
    with pytest.raises(ValueError):
        compute_water_mask(sample_image, {'l2w_mask_threshold': -1})
```

### Contribution Workflow

1. **Fork** the repository
2. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/new-feature
   ```
3. **Make descriptive commits:**
   ```bash
   git commit -m "feat: add algae detection algorithm"
   ```
4. **Push** to your fork:
   ```bash
   git push origin feature/new-feature
   ```
5. **Create a Pull Request** on GitHub

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting (no code change)
- `refactor`: Refactoring
- `test`: Add/modify tests
- `chore`: Maintenance

**Examples:**

```bash
feat(water_quality): add Castagna algorithm for TSS

fix(correction): fix LUT interpolation at edges
  
docs(api): update usage examples for ACOLITE class

test(utils): add tests for mask functions
```

### Pull Request Guidelines

**Checklist before PR:**

- [ ] Code follows PEP 8 style
- [ ] Tests added for new features
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Complete docstrings
- [ ] CHANGELOG.md updated

**PR Template:**

```markdown
## Description
[Description of changes]

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] No linter warnings

## How to Test
[Steps to test the changes]

## Screenshots (if applicable)
[Screenshots]
```

## Related Issues
Closes #[issue number]
```

## Documentation

### Build Documentation Locally

```bash
# Install dependencies
pip install mkdocs mkdocs-material mkdocstrings[python] mkdocs-mermaid2-plugin

# Serve locally (with auto-reload)
mkdocs serve

# Open in browser
# http://127.0.0.1:8000
```

### Add New Page

1. Create `.md` file in `docs/`
2. Add to `nav` in `mkdocs.yml`:

```yaml
nav:
  - Home: index.md
  - New Section:
      - New Page: path/to/page.md
```

### Writing Documentation

```markdown
# Page Title

Brief description.

## Section

Content...

### Subsection

```python
# Code example
from gee_acolite import ACOLITE
```

!!! note "Note"
    Additional information

!!! warning "Warning"
    Something important

!!! tip "Tip"
    Best practice
```

## Community

### Code of Conduct

We expect all contributors to:

- Be respectful and considerate
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards other members

### Communication

- **GitHub Issues**: For bugs and features
- **GitHub Discussions**: For questions and discussions
- **Email**: [your-email@example.com] for private inquiries

### Credits

Thanks to all contributors:

- See [Contributors](https://github.com/Aouei/gee_acolite/graphs/contributors)
- This project uses [ACOLITE](https://github.com/acolite/acolite) by Q. Vanhellemont

## Resources for Contributors

### Useful Links

- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Writing Good Commit Messages](https://chris.beams.io/posts/git-commit/)
- [Python Packaging Guide](https://packaging.python.org/)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/)

### Recommended Tutorials

- [Google Earth Engine Python API](https://developers.google.com/earth-engine/tutorials/community/intro-to-python-api)
- [ACOLITE Documentation](https://github.com/acolite/acolite/wiki)
- [Pytest Tutorial](https://docs.pytest.org/en/stable/getting-started.html)

## Frequently Asked Questions

### How do I start contributing?

1. Read the documentation
2. Look for issues labeled `good first issue`
3. Comment on the issue you want to work on
4. Fork and start coding

### What do I need to know?

- Basic/intermediate Python
- Basic Git
- Google Earth Engine (can be learned along the way)
- ACOLITE (optional, documentation helps)

### How long does it take to review a PR?

We try to review PRs within 1-2 weeks. If there is no response, feel free to remind us.

### Can I contribute without knowing how to code?

Yes! You can:
- Improve documentation
- Report bugs
- Suggest features
- Help other users

## Acknowledgments

Thank you for considering contributing to GEE ACOLITE! 🎉

Your help makes this project better for everyone.
