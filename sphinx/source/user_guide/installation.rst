Installation
============

Requirements
------------

* Python >= 3.8
* Google Earth Engine account
* ACOLITE (included)

Install from GitHub
-------------------

.. code-block:: bash

   git clone https://github.com/Aouei/gee_acolite.git
   cd gee_acolite
   pip install -e .

Dependencies
------------

Main dependencies installed automatically:

* earthengine-api
* numpy
* pandas
* xarray
* rasterio

Google Earth Engine Setup
--------------------------

Authenticate with Google Earth Engine:

.. code-block:: python

   import ee
   ee.Authenticate()
   ee.Initialize()
