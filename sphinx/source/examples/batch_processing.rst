Batch Processing
================

Process multiple images efficiently.

.. code-block:: python

   collection = search_images(aoi, '2023-01-01', '2023-12-31', 'sentinel2')
   
   def correct_image(image):
       return apply_acolite(image, aoi)
   
   corrected_collection = collection.map(correct_image)
