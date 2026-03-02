# Installation

## Requirements

| Requirement | Minimum |
|-------------|---------|
| Python | >= 3.11 |
| OS | Windows, Linux, macOS |
| Internet | Required (GEE API calls) |

---

## Install gee_acolite

```bash
pip install gee_acolite
```

---

## ACOLITE

`gee_acolite` uses ACOLITE internally for LUT loading and atmospheric calculations. ACOLITE is **not** distributed via PyPI and must be obtained separately from its [official repository](https://github.com/acolite/acolite).

Once downloaded, add it to your Python path before importing:

=== "Python script"

    ```python
    import sys
    sys.path.append('/path/to/acolite')

    import acolite as ac
    from gee_acolite import ACOLITE
    ```

=== "Jupyter notebook"

    ```python
    import sys
    sys.path.append('/path/to/acolite')

    import acolite as ac
    from gee_acolite import ACOLITE
    ```

Replace `/path/to/acolite` with the actual location of the ACOLITE folder on your system.

---

## Google Earth Engine

A GEE account and a Cloud Project are required. If you have not authenticated yet:

```bash
earthengine authenticate
```

Or from Python:

```python
import ee
ee.Authenticate()
ee.Initialize(project='your-cloud-project-id')
```

---

## Verify Installation

```python
import sys
sys.path.append('/path/to/acolite')

import ee
import acolite as ac
from gee_acolite import ACOLITE

ee.Initialize(project='your-cloud-project-id')
ac_gee = ACOLITE(ac, {})
print('Installation OK')
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'acolite'`

The ACOLITE path has not been added to `sys.path`. Add the following line before any import:

```python
import sys
sys.path.append('/path/to/acolite')
```

### `EEException: Please authorize access to your Earth Engine account`

Run authentication:

```bash
earthengine authenticate
```

---

## Next Steps

- [Quickstart](quickstart.md): Your first atmospheric correction
- [Configuration](configuration.md): Full settings reference
