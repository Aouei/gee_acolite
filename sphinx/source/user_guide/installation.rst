Installation
============

Requirements
------------

* Python >= 3.8
<<<<<<< HEAD
* Google Earth Engine account
* ACOLITE (included)
=======
* Google Earth Engine account and authentication
* ACOLITE (included in the package)
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0

Install from GitHub
-------------------

.. code-block:: bash

   git clone https://github.com/Aouei/gee_acolite.git
   cd gee_acolite
   pip install -e .

<<<<<<< HEAD
Dependencies
------------

Main dependencies installed automatically:
=======
Install from PyPI
-----------------

.. code-block:: bash

   pip install gee_acolite

Dependencies
------------

The main dependencies will be installed automatically:
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0

* earthengine-api
* numpy
* pandas
* xarray
* rasterio

<<<<<<< HEAD
Google Earth Engine Setup
--------------------------

Authenticate with Google Earth Engine:
=======
Setting up Google Earth Engine
-------------------------------

Before using gee_acolite, you need to authenticate with Google Earth Engine:
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0

.. code-block:: python

   import ee
   ee.Authenticate()
   ee.Initialize()
<<<<<<< HEAD
=======

For more information, visit the `Google Earth Engine documentation <https://developers.google.com/earth-engine/guides/python_install>`_.
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0
