import ee


def mask_negative_reflectance(image : ee.Image, band : str) -> ee.Image:
    return image.updateMask(image.select(band).gte(0)).rename(band)

def toa_mask(image : ee.Image, band : str = 'rhot_B11', threshold : float = 0.03):
    return image.select(band).lt(threshold)

def cirrus_mask(image : ee.Image, band : str = 'rhot_B10', threshold : float = 0.005):
    return image.select(band).lt(threshold)

def non_water(image : ee.Image, band : str = 'rhot_B11', threshold : float = 0.05) -> ee.Image:
    return image.select(band).lt(threshold)