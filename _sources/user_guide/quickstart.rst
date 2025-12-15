Quick Start
===========

<<<<<<< HEAD
Basic atmospheric correction example.
=======
This guide will help you get started with gee_acolite.

Basic Usage
-----------

Here's a simple example of how to use gee_acolite for atmospheric correction:
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0

.. code-block:: python

   import ee
   import gee_acolite
<<<<<<< HEAD
   from gee_acolite.utils.search import search_images
   from gee_acolite.correction import apply_acolite
=======
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0
   
   # Initialize Earth Engine
   ee.Initialize()
   
<<<<<<< HEAD
   # Define area of interest
   aoi = ee.Geometry.Rectangle([-122.5, 37.5, -122.0, 38.0])
   
   # Search for images
=======
   # Define your area of interest
   aoi = ee.Geometry.Rectangle([-122.5, 37.5, -122.0, 38.0])
   
   # Search for Sentinel-2 imagery
   from gee_acolite.utils.search import search_images
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0
   images = search_images(
       aoi=aoi,
       start_date='2023-01-01',
       end_date='2023-12-31',
       sensor='sentinel2'
   )
   
<<<<<<< HEAD
   # Apply correction
   corrected = apply_acolite(images.first(), aoi)
=======
   # Apply atmospheric correction
   from gee_acolite.correction import apply_acolite
   corrected = apply_acolite(images.first(), aoi)
   
   # View the result
   print(corrected.bandNames().getInfo())

Water Quality Analysis
----------------------

Calculate water quality parameters from corrected imagery:

.. code-block:: python

   from gee_acolite.water_quality import calculate_chl_a, calculate_turbidity
   
   # Calculate chlorophyll-a concentration
   chl_a = calculate_chl_a(corrected)
   
   # Calculate turbidity
   turbidity = calculate_turbidity(corrected)

Bathymetry Estimation
---------------------

Estimate satellite-derived bathymetry:

.. code-block:: python

   from gee_acolite.bathymetry import estimate_depth
   
   # Estimate water depth
   depth = estimate_depth(corrected, method='stumpf')

Next Steps
----------

* Check out the :doc:`../examples/basic_usage` for more detailed examples
* Explore the :doc:`../modules/correction` API documentation
* Learn about :doc:`../modules/water_quality` parameters
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0
