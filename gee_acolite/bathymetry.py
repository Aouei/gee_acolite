import ee

def multi_image(images: ee.ImageCollection, band: str = 'pSDB_green') -> ee.Image:
    return images.qualityMosaic(band)