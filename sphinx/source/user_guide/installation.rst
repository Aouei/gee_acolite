Installation
============

Requirements
------------

* Python >= 3.8
* Google Earth Engine account and authentication
* ACOLITE (included in the package)

Install from GitHub
-------------------

.. code-block:: bash

   git clone https://github.com/Aouei/gee_acolite.git
   cd gee_acolite
   pip install -e .

Install from PyPI
-----------------

.. code-block:: bash

   pip install gee_acolite

Dependencies
------------

The main dependencies will be installed automatically:

* earthengine-api
* numpy
* pandas
* xarray
* rasterio

Setting up Google Earth Engine
-------------------------------

Before using gee_acolite, you need to authenticate with Google Earth Engine:

.. code-block:: python

   import ee
   ee.Authenticate()
   ee.Initialize()

For more information, visit the `Google Earth Engine documentation <https://developers.google.com/earth-engine/guides/python_install>`_.
