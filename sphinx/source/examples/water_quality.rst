<<<<<<< HEAD
Water Quality
=============

Calculate water quality parameters.

.. code-block:: python

   from gee_acolite.water_quality import calculate_chl_a, calculate_turbidity
=======
Water Quality Example
=====================

Calculate water quality parameters from atmospherically corrected imagery.

Chlorophyll-a Concentration
----------------------------

.. code-block:: python

   import ee
   from gee_acolite.correction import apply_acolite
   from gee_acolite.water_quality import calculate_chl_a
   
   # Initialize Earth Engine
   ee.Initialize()
   
   # Load and correct an image (see basic_usage for details)
   aoi = ee.Geometry.Point([-122.3, 37.8])
   image = ee.Image('COPERNICUS/S2/20230615T184919_20230615T185919_T10SEG')
   corrected = apply_acolite(image, aoi)
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0
   
   # Calculate chlorophyll-a
   chl_a = calculate_chl_a(corrected)
   
<<<<<<< HEAD
   # Calculate turbidity
   turbidity = calculate_turbidity(corrected)
=======
   # Visualization
   vis_params = {
       'min': 0,
       'max': 10,
       'palette': ['blue', 'cyan', 'lime', 'yellow', 'red']
   }
   
   Map.addLayer(chl_a, vis_params, 'Chlorophyll-a (μg/L)')

Turbidity
---------

.. code-block:: python

   from gee_acolite.water_quality import calculate_turbidity
   
   # Calculate turbidity
   turbidity = calculate_turbidity(corrected)
   
   # Visualization
   turb_vis = {
       'min': 0,
       'max': 50,
       'palette': ['darkblue', 'blue', 'green', 'yellow', 'orange', 'red']
   }
   
   Map.addLayer(turbidity, turb_vis, 'Turbidity (NTU)')

Suspended Particulate Matter
-----------------------------

.. code-block:: python

   from gee_acolite.water_quality import calculate_spm
   
   # Calculate SPM
   spm = calculate_spm(corrected)
   
   # Visualization
   spm_vis = {
       'min': 0,
       'max': 100,
       'palette': ['navy', 'blue', 'cyan', 'lime', 'yellow', 'red']
   }
   
   Map.addLayer(spm, spm_vis, 'SPM (mg/L)')

Batch Processing Multiple Parameters
-------------------------------------

.. code-block:: python

   from gee_acolite.water_quality import (
       calculate_chl_a,
       calculate_turbidity,
       calculate_spm
   )
   
   # Process all parameters
   params = {
       'chl_a': calculate_chl_a(corrected),
       'turbidity': calculate_turbidity(corrected),
       'spm': calculate_spm(corrected)
   }
   
   # Export all as separate bands
   combined = ee.Image.cat([
       params['chl_a'].rename('chl_a'),
       params['turbidity'].rename('turbidity'),
       params['spm'].rename('spm')
   ])
   
   # Export to Drive
   task = ee.batch.Export.image.toDrive(
       image=combined,
       description='water_quality_params',
       folder='GEE_exports',
       scale=10,
       region=aoi
   )
   task.start()
>>>>>>> d1148d8274bf86e59c80f80279b75d4845ad74c0
