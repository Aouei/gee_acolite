"""
Bathymetry utilities for satellite-derived bathymetry (SDB) processing.
"""
import ee


def multi_image(images: ee.ImageCollection, band: str = 'pSDB_green') -> ee.Image:
    """
    Create a quality mosaic from multiple images based on a bathymetry band.
    
    Selects the best pixel values from a collection of images based on the
    quality of a specified bathymetry band (e.g., pseudo-Satellite Derived Bathymetry).
    
    Parameters
    ----------
    images : ee.ImageCollection
        Collection of images containing bathymetry bands.
    band : str, optional
        Band name to use for quality assessment (default: 'pSDB_green').
        Pixels with higher values in this band are prioritized.
    
    Returns
    -------
    ee.Image
        Quality mosaic image with the best pixels from the collection.
    
    Examples
    --------
    >>> images = ee.ImageCollection([image1, image2, image3])
    >>> mosaic = multi_image(images, band='pSDB_red')
    """
    return images.qualityMosaic(band)