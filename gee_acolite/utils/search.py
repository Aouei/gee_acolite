"""
Image search and retrieval utilities for Google Earth Engine.

Provides functions to search and retrieve Sentinel-2 imagery from
the GEE catalog, with optional cloud probability data integration.
"""
import ee

from typing import Optional


def search(roi : ee.Geometry, start : str, end : str, 
           collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    """
    Search for Sentinel-2 images in a region and time period.
    
    Parameters
    ----------
    roi : ee.Geometry
        Region of interest.
    start : str
        Start date in format 'YYYY-MM-DD'.
    end : str
        End date in format 'YYYY-MM-DD'.
    collection : str, optional
        Sentinel-2 collection name (default: 'S2_HARMONIZED').
        Options: 'S2_HARMONIZED', 'S2', 'S2_SR', 'S2_SR_HARMONIZED'.
    tile : str, optional
        Specific tile identifier to filter (e.g., 'T30SYJ').
    
    Returns
    -------
    ee.ImageCollection
        Collection of matching Sentinel-2 images.
    """
    if tile is None:
        sentinel2_l1 = ee.ImageCollection(f'COPERNICUS/{collection}').filterBounds(roi).filterDate(start, end)
    else:
        sentinel2_l1 = ee.ImageCollection(f'COPERNICUS/{collection}').filterBounds(roi).filterDate(start, end).filter(ee.Filter.stringContains('PRODUCT_ID', tile))

    return sentinel2_l1

def search_list(roi : ee.Geometry, starts : list[str], ends : list[str], 
                collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    """
    Search for multiple Sentinel-2 images using date pairs.
    
    Retrieves the first image matching each date range. Useful for
    selecting specific acquisitions.
    
    Parameters
    ----------
    roi : ee.Geometry
        Region of interest.
    starts : list of str
        List of start dates in format 'YYYY-MM-DD'.
    ends : list of str
        List of end dates in format 'YYYY-MM-DD'.
    collection : str, optional
        Sentinel-2 collection name (default: 'S2_HARMONIZED').
    tile : str, optional
        Specific tile identifier to filter.
    
    Returns
    -------
    ee.ImageCollection
        Collection with first image from each date range.
    """
    return ee.ImageCollection.fromImages([search(roi, start, end, collection, tile).first() for start, end in zip(starts, ends)])


def search_with_cloud_proba(roi : ee.Geometry, start : str, end : str, 
                            collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    """
    Search Sentinel-2 images and join with Cloud Probability data.
    
    Retrieves Sentinel-2 images and joins them with the corresponding
    cloud probability data from COPERNICUS/S2_CLOUD_PROBABILITY.
    
    Parameters
    ----------
    roi : ee.Geometry
        Region of interest.
    start : str
        Start date in format 'YYYY-MM-DD'.
    end : str
        End date in format 'YYYY-MM-DD'.
    collection : str, optional
        Sentinel-2 collection name (default: 'S2_HARMONIZED').
    tile : str, optional
        Specific tile identifier to filter.
    
    Returns
    Search multiple Sentinel-2 images and join with Cloud Probability.
    
    Retrieves the first image matching each date range and joins with
    cloud probability data.
    
    Parameters
    ----------
    roi : ee.Geometry
        Region of interest.
    starts : list of str
        List of start dates in format 'YYYY-MM-DD'.
    ends : list of str
        List of end dates in format 'YYYY-MM-DD'.
    collection : str, optional
        Sentinel-2 collection name (default: 'S2_HARMONIZED').
    tile : str, optional
        Specific tile identifier to filter.
    
    Join Sentinel-2 collection with Cloud Probability data.
    
    Matches each Sentinel-2 image with its corresponding cloud probability
    image from the COPERNICUS/S2_CLOUD_PROBABILITY collection using the
    system:index property.
    
    Parameters
    ----------
    s2_collection : ee.ImageCollection
        Sentinel-2 L1C image collection.
    
    Returns
    -------
    ee.ImageCollection
        Collection with Cloud Probability images added as 'cloud_prob' property.
        starts: Lista de fechas de inicio (formato 'YYYY-MM-DD')
        ends: Lista de fechas de fin (formato 'YYYY-MM-DD')
        collection: Nombre de la colección de Sentinel-2 (default: 'S2_HARMONIZED')
        tile: Identificador del tile (opcional)
        
    Returns:
        Colección de imágenes con Cloud Probability unida
    """
    s2_collection = search_list(roi, starts, ends, collection, tile)
    return join_s2_with_cloud_prob(s2_collection)


def join_s2_with_cloud_prob(s2_collection : ee.ImageCollection) -> ee.ImageCollection:
    """
    Une la colección Sentinel-2 con Cloud Probability
    
    Args:
        s2_collection: Colección de imágenes Sentinel-2 L1C
        roi: Región de interés
        
    Returns:
        Colección de imágenes con Cloud Probability unida como propiedad 'cloud_prob'
    """
    
    def add_cloud_prob(img):
        img_index = img.get('system:index')
        cloud = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY') \
            .filter(ee.Filter.equals('system:index', img_index)) \
            .first()
        
        return img.set('cloud_prob', cloud)
    
    return s2_collection.map(add_cloud_prob)