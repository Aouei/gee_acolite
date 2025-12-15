Basic Usage
===========

Complete atmospheric correction workflow.

.. code-block:: python

   import ee
   from gee_acolite.utils.search import search_images
   from gee_acolite.correction import apply_acolite
   
   ee.Initialize()
   
   aoi = ee.Geometry.Rectangle([-122.5, 37.5, -122.0, 38.0])
   
   collection = search_images(
       aoi=aoi,
       start_date='2023-06-01',
       end_date='2023-06-30',
       sensor='sentinel2',
       max_cloud_cover=10
   )
   
   corrected = apply_acolite(collection.first(), aoi)
