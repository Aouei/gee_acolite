Water Quality
=============

Calculate water quality parameters.

.. code-block:: python

   from gee_acolite.water_quality import calculate_chl_a, calculate_turbidity
   
   # Calculate chlorophyll-a
   chl_a = calculate_chl_a(corrected)
   
   # Calculate turbidity
   turbidity = calculate_turbidity(corrected)
