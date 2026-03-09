# Contributing

Thank you for considering contributing to GEE ACOLITE! This guide explains how to
report issues, propose features, and submit code or documentation improvements.

## Ways to Contribute

### 🐛 Report Bugs

Before opening a new issue, check whether it has already been reported in
[Issues](https://github.com/Aouei/gee_acolite/issues). If not, create one including:

- A clear description of the problem
- Minimal reproducible code
- Full traceback
- Environment details (see template below)

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
- OS: [e.g., Ubuntu 22.04, Windows 11]
- Python: [e.g., 3.11.0]
- gee_acolite: [e.g., 1.2.0]
- ACOLITE: [e.g., 20231023]
- earthengine-api: [e.g., 0.1.390]

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

Open a [GitHub Issue](https://github.com/Aouei/gee_acolite/issues) and describe:

1. The use case and motivation
2. The expected behavior
3. A usage example if possible

### 📝 Improve Documentation

- Fix typos or unclear explanations
- Add usage examples or notebooks
- Improve API docstrings

### 💻 Contribute Code

See the [Development](#development) section below.

## Development

### Setting Up the Development Environment

GEE ACOLITE uses ACOLITE as a Git submodule. Make sure to initialise it after cloning:

```bash
# Fork and clone
git clone https://github.com/your-username/gee_acolite.git
cd gee_acolite

# Initialise the ACOLITE submodule
git submodule update --init --recursive

# Create and activate a virtual environment (Python >= 3.11 required)
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows

# Install the package in development mode
pip install -e .

# Optional: install visualisation dependencies
pip install -e ".[viz]"
```

!!! note "Conda users"
    If you use conda, you can create an environment with:
    ```bash
    conda create -n gee_acolite python=3.11
    conda activate gee_acolite
    pip install -e .
    ```

### Project Structure

```
gee_acolite/
├── gee_acolite/              # Source code
│   ├── __init__.py
│   ├── correction.py         # ACOLITE class — main DSF workflow
│   ├── water_quality.py      # Water quality products (SPM, Chl-a, Rrs…)
│   ├── bathymetry.py         # Satellite-derived bathymetry (SDB)
│   ├── utils/
│   │   ├── l1_convert.py     # DN → TOA, geometry, resampling
│   │   ├── masks.py          # Water / cloud / shadow masking
│   │   └── search.py         # Sentinel-2 search + cloud probability
│   └── sensors/
│       └── sentinel2.py      # Band definitions and scale groups
├── ACOLITE/                  # Git submodule (Vanhellemont)
├── tests/                    # Notebooks and scripts for manual testing
├── docs/                     # MkDocs documentation
├── pyproject.toml            # Package configuration
└── README.md
```

### Code Style

We follow [PEP 8](https://pep8.org/). Use NumPy-style docstrings and type hints:

```python
# Import order: stdlib → third-party → GEE → local
import os

import numpy as np
import scipy.interpolate

import ee

from gee_acolite.utils import masks


def compute_rrs(image: ee.Image, settings: dict) -> ee.Image:
    """
    Convert surface reflectance to remote sensing reflectance.

    Parameters
    ----------
    image : ee.Image
        L2W image containing ``rhos_B*`` bands.
    settings : dict
        ACOLITE settings dictionary.

    Returns
    -------
    ee.Image
        Image with ``Rrs_B*`` bands added.

    Examples
    --------
    >>> rrs_image = compute_rrs(l2w_image, settings)
    """
    ...
```

### Testing

Tests are organised as Jupyter notebooks under `tests/` and one standalone script
(`tests/test_tiled_mode.py`). To run the script:

```bash
python tests/test_tiled_mode.py
```

For notebook-based tests, open the relevant notebook in `tests/tests/` or `tests/SDB/`
and run all cells. GEE authentication is required:

```python
import ee
ee.Authenticate()
ee.Initialize(project="your-project-id")
```

When contributing new functionality, add a minimal notebook or extend an existing one
demonstrating the expected behaviour.

### Contribution Workflow

1. **Fork** the repository on GitHub
2. **Create a branch** for your change:
   ```bash
   git checkout -b feat/my-new-feature
   ```
3. **Commit** using [Conventional Commits](#commit-convention):
   ```bash
   git commit -m "feat(bathymetry): add multi-band SDB calibration"
   ```
4. **Push** to your fork:
   ```bash
   git push origin feat/my-new-feature
   ```
5. **Open a Pull Request** against `main`

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change with no new feature or fix |
| `test` | Add or update tests |
| `chore` | Maintenance (deps, CI, tooling) |

**Release tags** (append to commit message to trigger version bump in CI):

| Tag | Effect |
|---|---|
| `[release-patch]` | Bumps patch version (1.2.0 → 1.2.1) |
| `[release-minor]` | Bumps minor version (1.2.0 → 1.3.0) |
| `[skip ci]` | Skips CI entirely |

**Examples:**

```
feat(water_quality): add Dogliotti turbidity for B5

fix(correction): handle NaN values in dark spectrum retrieval

docs(api): update ACOLITE.correct() return type description

chore: bump earthengine-api dependency to >=0.1.390 [release-patch]
```

### Pull Request Guidelines

**Checklist before opening a PR:**

- [ ] Code follows PEP 8
- [ ] New functionality has a test notebook or script
- [ ] Docstrings are complete and use NumPy style
- [ ] Documentation updated if public API changed
- [ ] All existing tests/notebooks still work

**PR Template:**

```markdown
## Description
[What does this PR change and why?]

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation / refactor

## How to Test
[Steps or notebook to verify the change]

## Related Issues
Closes #[issue number]
```

## Documentation

### Build Locally

```bash
pip install mkdocs mkdocs-material mkdocstrings[python] mkdocs-mermaid2-plugin

# Live preview with auto-reload
mkdocs serve
# → http://127.0.0.1:8000
```

### Add a New Page

1. Create a `.md` file in `docs/`
2. Register it in `mkdocs.yml` under `nav`:

```yaml
nav:
  - Section:
      - New Page: path/to/page.md
```

### Admonitions

Use MkDocs Material admonitions to highlight important information:

```markdown
!!! note "GEE initialisation"
    Always call `ee.Initialize(project=...)` before using any GEE functionality.

!!! warning "ACOLITE submodule"
    ACOLITE must be initialised with `git submodule update --init --recursive`.

!!! tip "Dark spectrum"
    The `getInfo()` call for the dark spectrum is the only client-side bottleneck
    per image. Keep the collection small to reduce processing time.
```

## Community

### Code of Conduct

- Be respectful and constructive
- Accept and give feedback in good faith
- Focus on what is best for the project and its users

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions, ideas, and general conversation

## Frequently Asked Questions

### Do I need to know ACOLITE internals to contribute?

No. Most contributions involve GEE-side code (`correction.py`, `water_quality.py`,
`bathymetry.py`) which does not require deep knowledge of ACOLITE. The ACOLITE
interaction is isolated to LUT loading and dark spectrum retrieval in `correction.py`.

### What Python version is required?

Python >= 3.11 is required, matching the `requires-python` constraint in `pyproject.toml`.

### How do I authenticate with GEE?

```python
import ee
ee.Authenticate()            # only needed once
ee.Initialize(project="your-cloud-project")
```

See the [GEE Python quickstart](https://developers.google.com/earth-engine/guides/python_install)
for full instructions.

### My ACOLITE submodule is empty — what do I do?

```bash
git submodule update --init --recursive
```

If you cloned without `--recurse-submodules`, the `ACOLITE/` directory will be empty
until you run the command above.

---

Thank you for contributing to GEE ACOLITE!
