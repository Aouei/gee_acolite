Basic Usage Example
===================

This example demonstrates the basic workflow of using gee_acolite for atmospheric correction.

Complete Workflow
-----------------

.. code-block:: python

   import ee
   import gee_acolite
   from gee_acolite.utils.search import search_images
   from gee_acolite.correction import apply_acolite
   
   # Initialize Earth Engine
   ee.Initialize()
   
   # Define area of interest (example: San Francisco Bay)
   aoi = ee.Geometry.Rectangle([-122.5, 37.5, -122.0, 38.0])
   
   # Search for Sentinel-2 images
   collection = search_images(
       aoi=aoi,
       start_date='2023-06-01',
       end_date='2023-06-30',
       sensor='sentinel2',
       max_cloud_cover=10
   )
   
   print(f"Found {collection.size().getInfo()} images")
   
   # Get the first image
   image = collection.first()
   
   # Apply ACOLITE atmospheric correction
   corrected = apply_acolite(
       image=image,
       aoi=aoi,
       output_format='Rrs'  # Remote sensing reflectance
   )
   
   # Export the result
   task = ee.batch.Export.image.toDrive(
       image=corrected,
       description='acolite_corrected',
       folder='GEE_exports',
       scale=10,
       region=aoi,
       maxPixels=1e13
   )
   task.start()
   
   print("Export started!")

Visualization
-------------

.. code-block:: python

   # Create a visualization for true color
   vis_params = {
       'bands': ['B4', 'B3', 'B2'],
       'min': 0,
       'max': 0.3
   }
   
   # Display on a map (using geemap)
   import geemap
   
   Map = geemap.Map()
   Map.centerObject(aoi, 10)
   Map.addLayer(corrected, vis_params, 'Corrected Image')
   Map
