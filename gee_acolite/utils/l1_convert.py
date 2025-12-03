import ee
from functools import partial

from gee_acolite.sensors.sentinel2 import SENTINEL2_BANDS, BAND_BY_SCALE


def l1_to_rrs(images : ee.ImageCollection, scale: int) -> ee.ImageCollection:
    resample_scale = partial(resample, band = BAND_BY_SCALE.get(scale, 'B2'))
    return images.select(SENTINEL2_BANDS).map(DN_to_rrs).map(resample_scale)

def DN_to_rrs(image : ee.Image) -> ee.Image:
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
    return image.resample('bilinear').reproject(image.select(band).projection())