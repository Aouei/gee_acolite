# Examples

This directory contains example scripts demonstrating how to use GEE ACOLITE.

## Available Examples

### Basic Usage
- [`01_basic_usage.py`](01_basic_usage.py) - Simple atmospheric correction workflow
- [`02_water_quality.py`](02_water_quality.py) - Computing water quality parameters

### Advanced Usage
- [`03_batch_processing.py`](03_batch_processing.py) - Processing multiple images
- [`04_custom_settings.py`](04_custom_settings.py) - Customizing correction parameters
- [`05_export_results.py`](05_export_results.py) - Exporting corrected images to Google Drive

### Comparison Studies
- [`06_method_comparison.py`](06_method_comparison.py) - Comparing dark spectrum methods
- [`07_model_selection.py`](07_model_selection.py) - Different model selection criteria

## Running Examples

1. **Install dependencies:**
   ```bash
   pip install gee_acolite
   ```

2. **Initialize Earth Engine:**
   ```bash
   earthengine authenticate
   ```

3. **Run an example:**
   ```bash
   python examples/01_basic_usage.py
   ```

## Prerequisites

- Google Earth Engine account
- ACOLITE installed (see main README)
- Authenticated Earth Engine session

## Need Help?

- Check the [API Reference](../docs/)
- Open an issue on [GitHub](https://github.com/Aouei/gee_acolite/issues)
