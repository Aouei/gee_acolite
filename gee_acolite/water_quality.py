import numpy as np
import ee

import gee_acolite.utils.masks as masks
from gee_acolite.sensors.sentinel2 import SENTINEL2_BANDS


def compute_water_mask(image: ee.Image, settings: dict) -> ee.Image:
    mask = masks.non_water(image, 
                           threshold = settings.get('l2w_mask_threshold', 0.05))
    mask = mask.updateMask(masks.cirrus_mask(image, 
                                             threshold = settings.get('l2w_mask_cirrus_threshold', 0.005)))
    
    for band in SENTINEL2_BANDS:
        mask  = mask.updateMask( masks.toa_mask(image, 
                                                f'rhot_{band}', 
                                                settings.get('l2w_mask_high_toa_threshold', 0.3)) )
    return mask

def compute_water_bands(image: ee.Image, settings: dict) -> ee.Image:
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
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 342.10,
                                                            'C' : 0.19563, 
                                                            'red' : image.select('rhos_B4') }).rename('SPM_Nechad2016_665').toFloat()

def spm_nechad2016_704(image : ee.Image) -> ee.Image:
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 444.36,
                                                            'C' : 0.18753, 
                                                            'red' : image.select('rhos_B5') }).rename('SPM_Nechad2016_704').toFloat()

def spm_nechad2016_740(image : ee.Image) -> ee.Image:
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 1517.00,
                                                            'C' : 0.19736, 
                                                            'red' : image.select('rhos_B6') }).rename('SPM_Nechad2016_739').toFloat()

def tur_nechad2016_665(image : ee.Image) -> ee.Image:
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 366.14,
                                                            'C' : 0.19563, 
                                                            'red' : image.select('rhos_B4') }).rename('TUR_Nechad2016_665').toFloat()

def tur_nechad2016_704(image : ee.Image) -> ee.Image:
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 439.09,
                                                            'C' : 0.18753, 
                                                            'red' : image.select('rhos_B5') }).rename('TUR_Nechad2016_704').toFloat()

def tur_nechad2016_740(image : ee.Image) -> ee.Image:
    return image.expression('(A * red) / (1 - (red / C))', {'A' : 1590.66,
                                                            'C' : 0.19736, 
                                                            'red' : image.select('rhos_B6') }).rename('TUR_Nechad2016_739').toFloat()

def chl_oc2(image : ee.Image) -> ee.Image:
    A, B, C, D, E = 0.1977,-1.8117,1.9743,-2.5635,-0.7218 # TODO : interpolar B1 a las dimensiones de B2
    x = image.expression('log( x / y )', {'x' : image.select('rhos_B2'), 
                                          'y' : image.select('rhos_B3') }).rename('x')
    return image.expression('10 ** (A + B * x + C * (x**2) + D * (x**3) + E * (x**4) )', {'A' : A, 
                                                                                          'B' : B, 
                                                                                          'C' : C, 
                                                                                          'D' : D,
                                                                                          'E' : E,
                                                                                          'x' : x }).rename('chl_oc2').toFloat()

def chl_oc3(image : ee.Image) -> ee.Image:
    A, B, C, D, E = 0.2412,-2.0546,1.1776,-0.5538,-0.4570 # TODO : interpolar B1 a las dimensiones de B2
    x = image.expression('log( x / y )', {'x' : image.select('rhos_B2').max(image.select('rhos_B1')).rename('x'), 
                                          'y' : image.select('rhos_B3') }).rename('x')
    return image.expression('10 ** (A + B * x + C * (x**2) + D * (x**3) + E * (x**4) )', {'A' : A, 
                                                                                          'B' : B, 
                                                                                          'C' : C, 
                                                                                          'D' : D,
                                                                                          'E' : E,
                                                                                          'x' : x }).rename('chl_oc3').toFloat()

def chl_re_mishra(image : ee.Image) -> ee.Image:
    a, b, c = 14.039, 86.11, 194.325
    ndci = image.normalizedDifference(['rhos_B5', 'rhos_B4']).rename('ndci')
    return image.expression('a + b * ndci + c * ndci * ndci', {'a' : a, 
                                                               'b' : b, 
                                                               'c' : c, 
                                                               'ndci' : ndci }).rename('chl_re_mishra').toFloat()

def ndwi(image : ee.Image) -> ee.Image:
    return image.normalizedDifference(['Rrs_B3', 'Rrs_B8']).rename('ndwi').toFloat()

def pSDB_red(image : ee.Image) -> ee.Image:
    return image.expression('log(n * pi * blue) / log(n * pi * red)', {'n' : 1_000,
                                                                       'pi' : float(np.pi),
                                                                       'blue' : image.select('Rrs_B2'),
                                                                       'red' : image.select('Rrs_B4') }).rename('pSDB_red').toFloat()

def pSDB_green(image : ee.Image) -> ee.Image:
    return image.expression('log(n * pi * blue) / log(n * pi * green)', {'n' : 1_000,
                                                                         'pi' : float(np.pi),
                                                                         'blue' : image.select('Rrs_B2'),
                                                                         'green' : image.select('Rrs_B3') }).rename('pSDB_green').toFloat()

def rrs(image : ee.Image) -> ee.image:
    bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']
    return [ image.select(f'rhos_{band}').divide(np.pi).rename(f'Rrs_{band}').toFloat() for band in bands ]

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