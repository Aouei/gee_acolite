"""
Masking utilities for quality control and scene filtering.

Provides functions to create various masks for cloud detection,
water/land classification, and quality filtering.
"""
import ee


def mask_negative_reflectance(image : ee.Image, band : str) -> ee.Image:
    """
    Mask out negative reflectance values.
    
    Removes pixels with negative reflectance, which are physically
    impossible and indicate processing errors or noise.
    
    Parameters
    ----------
    image : ee.Image
        Image with reflectance band.
    band : str
        Band name to check for negative values.
    
    Returns
    -------
    ee.Image
        Masked image with only non-negative values.
    """
    return image.updateMask(image.select(band).gte(0)).rename(band)

def toa_mask(image : ee.Image, band : str = 'rhot_B11', threshold : float = 0.03):
    """
    Create mask based on TOA reflectance threshold.
    
    Masks pixels with high TOA reflectance, typically indicating
    clouds, bright surfaces, or other anomalies.
    
    Parameters
    ----------
    image : ee.Image
        Image with TOA reflectance bands.
    band : str, optional
        Band name to check (default: 'rhot_B11' - SWIR).
    threshold : float, optional
        Maximum reflectance threshold (default: 0.03).
    
    Returns
    -------
    ee.Image
        Binary mask (1 = valid, 0 = masked).
    """
    return image.select(band).lt(threshold)

def cirrus_mask(image : ee.Image, band : str = 'rhot_B10', threshold : float = 0.005):
    """
    Create cirrus cloud mask.
    
    Uses cirrus band (1375nm) to detect high-altitude cirrus clouds.
    
    Parameters
    ----------
    image : ee.Image
        Image with cirrus band.
    band : str, optional
        Cirrus band name (default: 'rhot_B10').
    threshold : float, optional
        Maximum cirrus reflectance (default: 0.005).
    
    Returns
    -------
    ee.Image
        Binary mask (1 = no cirrus, 0 = cirrus detected).
    """
    return image.select(band).lt(threshold)

def non_water(image : ee.Image, band : str = 'rhot_B11', threshold : float = 0.05) -> ee.Image:
    """
    Create water/land classification mask.
    
    Uses SWIR reflectance to distinguish water from land.
    Water has low SWIR reflectance due to strong absorption.
    
    Parameters
    ----------
    image : ee.Image
        Image with SWIR band.
    band : str, optional
        SWIR band name (default: 'rhot_B11').
    threshold : float, optional
        Maximum reflectance for water (default: 0.05).
    
    Returns
    -------
    ee.Image
        Binary mask (1 = water, 0 = land).
    """
    return image.select(band).lt(threshold)


def add_cloud_bands(img : ee.Image, cloud_prob_threshold : float = 50) -> ee.Image:
    """
    Add cloud mask band based on cloud probability.
    
    Uses Sentinel-2 Cloud Probability dataset to identify cloudy pixels.
    
    Parameters
    ----------
    img : ee.Image
        Image with 'cloud_prob' property containing Cloud Probability image.
    cloud_prob_threshold : float, optional
        Cloud probability threshold 0-100 (default: 50).
    
    Returns
    -------
    ee.Image
        Input image with 'clouds' band added (1 = cloud, 0 = clear).
    """
    # Get cloud probability (already as band)
    cld_prb = ee.Image(img.get('cloud_prob')).select('probability')
    
    # Cloud mask based on probability threshold
    is_cloud = cld_prb.gt(cloud_prob_threshold).rename('clouds')
    
    return img.addBands(is_cloud)


def add_shadow_bands(img : ee.Image, nir_dark_threshold : float = 0.15, 
                     cloud_proj_distance : float = 1) -> ee.Image:
    """
    Add cloud shadow mask bands to L1C image.
    
    Identifies cloud shadows by projecting cloud locations in the direction
    of solar illumination and intersecting with dark NIR pixels.
    
    Parameters
    ----------
    img : ee.Image
        Image with 'clouds' band and solar geometry metadata.
    nir_dark_threshold : float, optional
        Threshold for dark pixels in NIR (0-1, default: 0.15).
    cloud_proj_distance : float, optional
        Maximum shadow projection distance in km (default: 1).
    
    Returns
    -------
    ee.Image
        Input image with 'dark_pixels', 'cloud_transform', and 'shadows' bands.
    """
    # Dark pixels in NIR (possible shadows) - for L1C use B8 directly
    dark_pixels = img.select('rhot_B8').lt(nir_dark_threshold * 10000).rename('dark_pixels')
    
    # Shadow projection direction
    shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')))
    
    # Project shadows from clouds
    cld_proj = img.select('clouds').directionalDistanceTransform(shadow_azimuth, cloud_proj_distance * 10) \
        .reproject(**{'crs': img.select(0).projection(), 'scale': 100}) \
        .select('distance') \
        .mask() \
        .rename('cloud_transform')
    
    # Identify shadows as intersection of dark pixels and cloud projection
    shadows = cld_proj.multiply(dark_pixels).rename('shadows')
    
    return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))


def add_cld_shdw_mask(img : ee.Image, cloud_prob_threshold : float = 50, 
                      nir_dark_threshold : float = 0.15, cloud_proj_distance : float = 1, 
                      buffer : int = 50) -> ee.Image:
    """
    Add combined cloud and shadow mask with buffer.
    
    Creates comprehensive cloud and shadow mask by combining:
    1. Cloud probability mask
    2. Cloud shadow detection
    3. Buffer around masked areas
    
    Parameters
    ----------
    img : ee.Image
        Image with 'cloud_prob' property containing Cloud Probability data.
    cloud_prob_threshold : float, optional
        Cloud probability threshold 0-100 (default: 50).
    nir_dark_threshold : float, optional
        Threshold for dark NIR pixels 0-1 (default: 0.15).
    cloud_proj_distance : float, optional
        Shadow projection distance in km (default: 1).
    buffer : int, optional
        Buffer distance around clouds/shadows in meters (default: 50).
    
    Returns
    -------
    ee.Image
        Input image with 'cloudmask' band (1 = cloud/shadow, 0 = clear).
    """
    # Add cloud bands
    img_cloud = add_cloud_bands(img, cloud_prob_threshold)
    
    # Add shadow bands
    img_cloud_shadow = add_shadow_bands(img_cloud, nir_dark_threshold, cloud_proj_distance)
    
    # Combine masks
    is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)
    
    # Apply buffer
    is_cld_shdw = is_cld_shdw.focal_min(2).focal_max(buffer * 2 / 20) \
        .reproject(**{'crs': img.select([0]).projection(), 'scale': 20}) \
        .rename('cloudmask')
    
    return img_cloud_shadow.addBands(is_cld_shdw)


def cld_shdw_mask(img : ee.Image) -> ee.Image:
    """
    Extract cloud/shadow mask for application.
    
    Inverts the 'cloudmask' band so that valid pixels = 1.
    
    Parameters
    ----------
    img : ee.Image
        Image with 'cloudmask' band.
    
    Returns
    -------
    ee.Image
        Binary mask (1 = valid/clear, 0 = cloud/shadow).
    """
    # Get inverted mask (1 = valid, 0 = masked)
    return img.select('cloudmask').Not()