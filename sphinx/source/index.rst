Welcome to gee_acolite's documentation!
========================================

**gee_acolite** is a Python package that integrates ACOLITE atmospheric correction with Google Earth Engine (GEE), 
enabling efficient processing of satellite imagery for water quality monitoring and bathymetry applications.

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   user_guide/installation

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   modules/correction
   modules/water_quality
   modules/bathymetry
   modules/utils

.. toctree::
   :maxdepth: 1
   :caption: Examples:

   examples/basic_usage


Features
--------

* **Atmospheric Correction**: Apply ACOLITE correction to GEE imagery
* **Water Quality**: Calculate water quality parameters from corrected imagery
* **Bathymetry**: Estimate satellite-derived bathymetry
* **Sensor Support**: Built-in support for Sentinel-2 and other sensors
* **Utilities**: Tools for image search, masking, and L1 conversion


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
