Batch Processing Example
========================

Process multiple images efficiently using gee_acolite.

Processing Multiple Images
---------------------------

.. code-block:: python

   import ee
   from gee_acolite.utils.search import search_images
   from gee_acolite.correction import apply_acolite
   
   # Initialize Earth Engine
   ee.Initialize()
   
   # Define area and time period
   aoi = ee.Geometry.Rectangle([-122.5, 37.5, -122.0, 38.0])
   start_date = '2023-01-01'
   end_date = '2023-12-31'
   
   # Search for images
   collection = search_images(
       aoi=aoi,
       start_date=start_date,
       end_date=end_date,
       sensor='sentinel2',
       max_cloud_cover=20
   )
   
   print(f"Processing {collection.size().getInfo()} images")
   
   # Apply correction to all images
   def correct_image(image):
       return apply_acolite(image, aoi)
   
   corrected_collection = collection.map(correct_image)

Time Series Analysis
--------------------

.. code-block:: python

   from gee_acolite.water_quality import calculate_chl_a
   
   # Calculate chlorophyll-a for each image
   def add_chl_a(image):
       chl = calculate_chl_a(image)
       return image.addBands(chl.rename('chl_a'))
   
   collection_with_chl = corrected_collection.map(add_chl_a)
   
   # Extract time series for a point
   point = ee.Geometry.Point([-122.3, 37.8])
   
   def extract_value(image):
       value = image.select('chl_a').reduceRegion(
           reducer=ee.Reducer.mean(),
           geometry=point,
           scale=10
       ).get('chl_a')
       
       return ee.Feature(None, {
           'date': image.date().format('YYYY-MM-dd'),
           'chl_a': value
       })
   
   time_series = collection_with_chl.map(extract_value)
   
   # Get as list
   data = time_series.aggregate_array('chl_a').getInfo()
   dates = time_series.aggregate_array('date').getInfo()
   
   # Plot with matplotlib
   import matplotlib.pyplot as plt
   
   plt.figure(figsize=(12, 6))
   plt.plot(dates, data, marker='o')
   plt.xlabel('Date')
   plt.ylabel('Chlorophyll-a (μg/L)')
   plt.title('Chlorophyll-a Time Series')
   plt.xticks(rotation=45)
   plt.grid(True)
   plt.tight_layout()
   plt.show()

Exporting Multiple Images
--------------------------

.. code-block:: python

   # Export each corrected image
   image_list = corrected_collection.toList(corrected_collection.size())
   
   for i in range(corrected_collection.size().getInfo()):
       image = ee.Image(image_list.get(i))
       date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
       
       task = ee.batch.Export.image.toDrive(
           image=image,
           description=f'corrected_{date}',
           folder='GEE_exports/batch',
           scale=10,
           region=aoi,
           maxPixels=1e13
       )
       task.start()
       print(f"Export started for {date}")

Creating Composite Images
--------------------------

.. code-block:: python

   # Create a median composite
   composite = corrected_collection.median()
   
   # Or use other reducers
   mean_composite = corrected_collection.mean()
   max_composite = corrected_collection.max()
   
   # Export composite
   task = ee.batch.Export.image.toDrive(
       image=composite,
       description='composite_2023',
       folder='GEE_exports',
       scale=10,
       region=aoi
   )
   task.start()
