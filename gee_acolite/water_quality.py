"""
Water quality parameter computation and masking.

This module provides functions to compute various water quality parameters
from atmospherically corrected satellite imagery, including:
- Suspended particulate matter (SPM)
- Turbidity
- Chlorophyll-a concentration
- Satellite-derived bathymetry (SDB)
- Remote sensing reflectance (Rrs)
"""
import numpy as np
import ee

import gee_acolite.utils.masks as masks
from gee_acolite.sensors.sentinel2 import SENTINEL2_BANDS


def compute_water_mask(image: ee.Image, settings: dict) -> ee.Image:
    """
    Create a comprehensive water mask for quality control.
    
    Combines multiple masking criteria to identify valid water pixels:
    - Water/land classification
    - Cirrus cloud contamination
    - High TOA reflectance (clouds, bright targets)
    - Optional cloud probability mask
    
    Parameters
    ----------
    image : ee.Image
        Atmospherically corrected image with TOA and surface reflectance bands.
    settings : dict
        Processing settings including mask thresholds.
    
    Returns
    -------
    ee.Image
        Binary mask where valid water pixels = 1.
    """
    mask = masks.non_water(image, 
                           threshold = settings.get('l2w_mask_threshold', 0.05))
    mask = mask.updateMask(masks.cirrus_mask(image, 
                                             threshold = settings.get('l2w_mask_cirrus_threshold', 0.005)))
    
    for band in SENTINEL2_BANDS:
        mask = mask.updateMask( masks.toa_mask(image, 
                                                f'rhot_{band}', 
                                                settings.get('l2w_mask_high_toa_threshold', 0.3)) )
        
    if settings.get('s2_cloud_proba', False):
        CLOUD_PROB_THRESHOLD = int(settings.get('s2_cloud_proba__cloud_threshold', 50))
        NIR_DARK_THRESHOLD = float(settings.get('s2_cloud_proba__nir_dark_threshold', 0.15))
        CLOUD_PROJ_DISTANCE = int(settings.get('s2_cloud_proba__cloud_proj_distance', 10))
        BUFFER = int(settings.get('s2_cloud_proba__buffer', 50))
        mask = mask.updateMask(masks.cld_shdw_mask(masks.add_cld_shdw_mask(image, 
                                                                           CLOUD_PROB_THRESHOLD, 
                                                                           NIR_DARK_THRESHOLD, 
                                                                           CLOUD_PROJ_DISTANCE, 
                                                                           BUFFER)))

    return mask

def compute_water_bands(image: ee.Image, settings: dict) -> ee.Image:
    """
    Compute water quality parameters and add them as bands.
    
    Applies water mask and computes selected water quality parameters
    based on settings configuration.
    
    Parameters
    ----------
    image : ee.Image
        Atmospherically corrected image with surface reflectance bands.
    settings : dict
        Processing settings including 'l2w_parameters' list.
    
    Returns
    -------
    ee.Image
        Input image with added water quality parameter bands.
    """
    mask = compute_water_mask(image, settings)

    for product in settings['l2w_parameters']:
        new_band = PRODUCTS[product](image)
        
        if isinstance(new_band, list):
            new_band = [band.updateMask(mask) for band in new_band]
        else:
            new_band = new_band.updateMask(mask)
        
        image = image.addBands(new_band)
    
    return image


def spm_nechad2016_665(image : ee.Image) -> ee.Image:
    """
    Compute suspended particulate matter using Nechad et al. (2016) algorithm at 665nm.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance band 'rhos_B4' (red band at 665nm).
    
    Returns
    -------
    ee.Image
        SPM concentration in mg/L.
    
    References
    ----------
    Nechad et al. (2016). Calibration and validation of a generic multisensor
    algorithm for mapping of total suspended matter in turbid waters.
    Remote Sensing of Environment, 159, 139-152.
    """
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 342.10,
                                                            'C' : 0.19563, 
                                                            'red' : image.select('rhos_B4') }).rename('SPM_Nechad2016_665').toFloat()

def spm_nechad2016_704(image : ee.Image) -> ee.Image:
    """
    Compute suspended particulate matter using Nechad et al. (2016) algorithm at 704nm.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance band 'rhos_B5' (red edge at 704nm).
    
    Returns
    -------
    ee.Image
        SPM concentration in mg/L.
    """
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 444.36,
                                                            'C' : 0.18753, 
                                                            'red' : image.select('rhos_B5') }).rename('SPM_Nechad2016_704').toFloat()

def spm_nechad2016_740(image : ee.Image) -> ee.Image:
    """
    Compute suspended particulate matter using Nechad et al. (2016) algorithm at 740nm.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance band 'rhos_B6' (NIR at 740nm).
    
    Returns
    -------
    ee.Image
        SPM concentration in mg/L.
    """
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 1517.00,
                                                            'C' : 0.19736, 
                                                            'red' : image.select('rhos_B6') }).rename('SPM_Nechad2016_739').toFloat()

def tur_nechad2016_665(image : ee.Image) -> ee.Image:
    """
    Compute turbidity using Nechad et al. (2016) algorithm at 665nm.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance band 'rhos_B4' (red band at 665nm).
    
    Returns
    -------
    ee.Image
        Turbidity in FNU (Formazin Nephelometric Units).
    """
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 366.14,
                                                            'C' : 0.19563, 
                                                            'red' : image.select('rhos_B4') }).rename('TUR_Nechad2016_665').toFloat()

def tur_nechad2016_704(image : ee.Image) -> ee.Image:
    """
    Compute turbidity using Nechad et al. (2016) algorithm at 704nm.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance band 'rhos_B5' (red edge at 704nm).
    
    Returns
    -------
    ee.Image
        Turbidity in FNU (Formazin Nephelometric Units).
    """
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 439.09,
                                                            'C' : 0.18753, 
                                                            'red' : image.select('rhos_B5') }).rename('TUR_Nechad2016_704').toFloat()

def tur_nechad2016_740(image : ee.Image) -> ee.Image:
    """
    Compute turbidity using Nechad et al. (2016) algorithm at 740nm.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance band 'rhos_B6' (NIR at 740nm).
    
    Returns
    -------
    ee.Image
        Turbidity in FNU (Formazin Nephelometric Units).
    """
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 1590.66,
                                                            'C' : 0.19736, 
                                                            'red' : image.select('rhos_B6') }).rename('TUR_Nechad2016_739').toFloat()

def chl_oc2(image : ee.Image) -> ee.Image:
    """
    Compute chlorophyll-a concentration using OC2 algorithm.
    
    Two-band blue-green ratio algorithm for chlorophyll-a estimation.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance bands 'rhos_B2' (blue) and 'rhos_B3' (green).
    
    Returns
    -------
    ee.Image
        Chlorophyll-a concentration in mg/m³.
    
    Notes
    -----
    TODO: Interpolate B1 to B2 dimensions for improved accuracy.
    """
    A, B, C, D, E = 0.1977,-1.8117,1.9743,-2.5635,-0.7218
    x = image.expression('log( x / y )', {'x' : image.select('rhos_B2'), 
                                          'y' : image.select('rhos_B3') }).rename('x')
    return image.expression('10 ** (A + B * x + C * (x**2) + D * (x**3) + E * (x**4) )', {'A' : A, 
                                                                                          'B' : B, 
                                                                                          'C' : C, 
                                                                                          'D' : D,
                                                                                          'E' : E,
                                                                                          'x' : x }).rename('chl_oc2').toFloat()

def chl_oc3(image : ee.Image) -> ee.Image:
    """
    Compute chlorophyll-a concentration using OC3 algorithm.
    
    Three-band ratio algorithm using maximum of blue bands vs green.
    More robust than OC2 for varying water types.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance bands 'rhos_B1', 'rhos_B2' (blue),
        and 'rhos_B3' (green).
    
    Returns
    -------
    ee.Image
        Chlorophyll-a concentration in mg/m³.
    
    Notes
    -----
    TODO: Interpolate B1 to B2 dimensions for improved accuracy.
    """
    A, B, C, D, E = 0.2412,-2.0546,1.1776,-0.5538,-0.4570
    x = image.expression('log( x / y )', {'x' : image.select('rhos_B2').max(image.select('rhos_B1')).rename('x'), 
                                          'y' : image.select('rhos_B3') }).rename('x')
    return image.expression('10 ** (A + B * x + C * (x**2) + D * (x**3) + E * (x**4) )', {'A' : A, 
                                                                                          'B' : B, 
                                                                                          'C' : C, 
                                                                                          'D' : D,
                                                                                          'E' : E,
                                                                                          'x' : x }).rename('chl_oc3').toFloat()

def chl_re_mishra(image : ee.Image) -> ee.Image:
    """
    Compute chlorophyll-a concentration using red edge NDCI algorithm.
    
    Uses Normalized Difference Chlorophyll Index (NDCI) based on red edge
    bands. Particularly effective for turbid and productive waters.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance bands 'rhos_B5' (red edge at 704nm)
        and 'rhos_B4' (red at 665nm).
    
    Returns
    -------
    ee.Image
        Chlorophyll-a concentration in mg/m³.
    
    References
    ----------
    Mishra & Mishra (2012). Normalized difference chlorophyll index:
    A novel model for remote estimation of chlorophyll-a concentration in
    turbid productive waters. Remote Sensing of Environment, 117, 394-406.
    """
    a, b, c = 14.039, 86.11, 194.325
    ndci = image.normalizedDifference(['rhos_B5', 'rhos_B4']).rename('ndci')
    return image.expression('a + b * ndci + c * ndci * ndci', {'a' : a, 
                                                               'b' : b, 
                                                               'c' : c, 
                                                               'ndci' : ndci }).rename('chl_re_mishra').toFloat()

def ndwi(image : ee.Image) -> ee.Image:
    """
    Compute Normalized Difference Water Index.
    
    Parameters
    ----------
    image : ee.Image
        Image with remote sensing reflectance bands 'Rrs_B3' (green)
        and 'Rrs_B8' (NIR).
    
    Returns
    -------
    ee.Image
        NDWI values (range: -1 to 1).
    """
    return image.normalizedDifference(['Rrs_B3', 'Rrs_B8']).rename('ndwi').toFloat()

def pSDB_red(image : ee.Image) -> ee.Image:
    """
    Compute pseudo-Satellite Derived Bathymetry using blue-red ratio.
    
    Implements log-ratio bathymetry algorithm using blue and red bands.
    Provides relative depth estimation in clear shallow waters.
    
    Parameters
    ----------
    image : ee.Image
        Image with remote sensing reflectance bands 'Rrs_B2' (blue)
        and 'Rrs_B4' (red).
    
    Returns
    -------
    ee.Image
        Pseudo-bathymetry index (higher values = shallower water).
    """
    return image.expression('log(n * pi * blue) / log(n * pi * red)', {'n' : 1_000,
                                                                       'pi' : float(np.pi),
                                                                       'blue' : image.select('Rrs_B2'),
                                                                       'red' : image.select('Rrs_B4') }).rename('pSDB_red').toFloat()

def pSDB_green(image : ee.Image) -> ee.Image:
    """
    Compute pseudo-Satellite Derived Bathymetry using blue-green ratio.
    
    Implements log-ratio bathymetry algorithm using blue and green bands.
    Generally more sensitive in clearer waters compared to blue-red ratio.
    
    Parameters
    ----------
    image : ee.Image
        Image with remote sensing reflectance bands 'Rrs_B2' (blue)
        and 'Rrs_B3' (green).
    
    Returns
    -------
    ee.Image
        Pseudo-bathymetry index (higher values = shallower water).
    """
    return image.expression('log(n * pi * blue) / log(n * pi * green)', {'n' : 1_000,
                                                                         'pi' : float(np.pi),
                                                                         'blue' : image.select('Rrs_B2'),
                                                                         'green' : image.select('Rrs_B3') }).rename('pSDB_green').toFloat()

def rrs(image : ee.Image) -> ee.image:
    """
    Convert surface reflectance to remote sensing reflectance.
    
    Transforms surface reflectance (rhos) to remote sensing reflectance (Rrs)
    by dividing by π. Rrs is the standard unit for ocean color products.
    
    Parameters
    ----------
    image : ee.Image
        Image with surface reflectance bands (rhos_B*).
    
    Returns
    -------
    list of ee.Image
        List of Rrs bands for all Sentinel-2 bands.
    """
    bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']
    return [ image.select(f'rhos_{band}').divide(np.pi).rename(f'Rrs_{band}').toFloat() for band in bands ]

# Dictionary mapping product names to computation functions
PRODUCTS = {
    'spm_nechad2016' : spm_nechad2016_665,
    'spm_nechad2016_704' : spm_nechad2016_704,
    'spm_nechad2016_740' : spm_nechad2016_740,
    'tur_nechad2016' : tur_nechad2016_665,
    'tur_nechad2016_704' : tur_nechad2016_704,
    'tur_nechad2016_740' : tur_nechad2016_740,
    'chl_oc2' : chl_oc2,
    'chl_oc3' : chl_oc3,
    'chl_re_mishra' : chl_re_mishra,
    'pSDB_red' : pSDB_red,
    'pSDB_green' : pSDB_green,
    'Rrs_*' : rrs
}