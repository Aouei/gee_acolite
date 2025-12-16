"""
Level-1 to reflectance conversion utilities.

Provides functions to convert Sentinel-2 L1C Digital Numbers to
top-of-atmosphere (TOA) reflectance with proper geometric metadata.
"""
import ee
from functools import partial

from gee_acolite.sensors.sentinel2 import SENTINEL2_BANDS, BAND_BY_SCALE


def l1_to_rrs(images : ee.ImageCollection, scale: int) -> ee.ImageCollection:
    """
    Convert L1C image collection from DN to TOA reflectance.
    
    Applies DN to reflectance conversion and resamples all bands to
    the specified spatial resolution.
    
    Parameters
    ----------
    images : ee.ImageCollection
        Sentinel-2 L1C image collection with DN values.
    scale : int
        Target spatial resolution in meters (10, 20, or 60).
    
    Returns
    -------
    ee.ImageCollection
        Collection with TOA reflectance and geometry metadata.
    """
    resample_scale = partial(resample, band = BAND_BY_SCALE.get(scale, 'B2'))
    return images.select(SENTINEL2_BANDS).map(DN_to_rrs).map(resample_scale)

def DN_to_rrs(image : ee.Image) -> ee.Image:
    """
    Convert L1C image from Digital Numbers to TOA reflectance.
    
    Applies radiometric calibration (DN / 10000) and extracts viewing
    geometry from metadata (solar and viewing zenith/azimuth angles).
    Also computes relative azimuth angle.
    
    Parameters
    ----------
    image : ee.Image
        Sentinel-2 L1C image with DN values and angle metadata.
    
    Returns
    -------
    ee.Image
        Image with TOA reflectance (0-1) and geometry properties:
        'sza', 'saa', 'vza', 'vaa', 'raa'.
    """
    rrs = image.divide(10_000)

    rrs = rrs.set('sza', image.get('MEAN_SOLAR_ZENITH_ANGLE'))
    rrs = rrs.set('saa', image.get('MEAN_SOLAR_AZIMUTH_ANGLE'))
    rrs = rrs.set('vza', get_mean_band_angle(image, 'ZENITH'))
    rrs = rrs.set('vaa', get_mean_band_angle(image, 'AZIMUTH'))

    raa = ee.Number(rrs.get('saa')).subtract(rrs.get('vaa')).abs()

    raa = ee.Algorithms.If(raa.gt(180), raa.subtract(360).abs(), raa)
    rrs = rrs.set('raa', raa)
    rrs = rrs.set('PRODUCT_ID', ee.String(ee.String(image.get('PRODUCT_ID')).split('L1C').get(0)))

    rrs = rrs.set('system:time_start', image.get('system:time_start'))

    rrs = rrs.copyProperties(image)
    rrs = rrs.set('system:time_start', image.get('system:time_start'))

    return rrs

def get_mean_band_angle(image : ee.Image, angle_name : str) -> ee.Number:
    """
    Compute mean viewing angle across all bands.
    
    Extracts and averages band-specific viewing angles from Sentinel-2
    metadata. Each band has its own viewing geometry due to the sensor's
    detector layout.
    
    Parameters
    ----------
    image : ee.Image
        Sentinel-2 L1C image with angle metadata.
    angle_name : str
        Angle type to extract: 'ZENITH' or 'AZIMUTH'.
    
    Returns
    -------
    ee.Number
        Mean viewing angle across all bands (in degrees).
    """
    bands = image.bandNames()
    
    for index in range(13):
       bands = bands.set(index, ee.String('MEAN_INCIDENCE_' + angle_name + '_ANGLE_').cat(bands.get(index)))
    
    angle = ee.Number(0)
    for index in range(13):
       angle = angle.add(ee.Number(image.get(bands.get(index))))
    else:
        angle = angle.divide(image.bandNames().length())
    
    return angle

def resample(image : ee.Image, band: str) -> ee.Image:
    """
    Resample all bands to match a reference band's projection.
    
    Applies bilinear resampling to align all bands to the spatial
    resolution and projection of the specified reference band.
    
    Parameters
    ----------
    image : ee.Image
        Image with multiple bands at different resolutions.
    band : str
        Reference band name (e.g., 'B2' for 10m, 'B5' for 20m).
    
    Returns
    -------
    ee.Image
        Resampled image with all bands matching reference projection.
    """
    return image.resample('bilinear').reproject(image.select(band).projection())