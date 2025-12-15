Quick Start
===========

Basic atmospheric correction example.

.. code-block:: python

   import ee
   import gee_acolite
   from gee_acolite.utils.search import search_images
   from gee_acolite.correction import apply_acolite
   
   # Initialize Earth Engine
   ee.Initialize()
   
   # Define area of interest
   aoi = ee.Geometry.Rectangle([-122.5, 37.5, -122.0, 38.0])
   
   # Search for images
   images = search_images(
       aoi=aoi,
       start_date='2023-01-01',
       end_date='2023-12-31',
       sensor='sentinel2'
   )
   
   # Apply correction
   corrected = apply_acolite(images.first(), aoi)
