import ee

from typing import Optional


def search(roi : ee.Geometry, start : str, end : str, 
           collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    if tile is None:
        sentinel2_l1 = ee.ImageCollection(f'COPERNICUS/{collection}').filterBounds(roi).filterDate(start, end)
    else:
        sentinel2_l1 = ee.ImageCollection(f'COPERNICUS/{collection}').filterBounds(roi).filterDate(start, end).filter(ee.Filter.stringContains('PRODUCT_ID', tile))

    return sentinel2_l1

def search_list(roi : ee.Geometry, starts : str, ends : str, 
                collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    
    return ee.ImageCollection.from_images([search(roi, start, end, collection, tile).first() for start, end in zip(starts, ends)])