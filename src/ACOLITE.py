import numpy as np
import scipy.stats
import ee

from typing import List, Tuple, Optional
from acolite import ac, shared, aerlut


def search_with_clouds(roi : ee.Geometry, start : str, end : str, collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    if tile is None:
        sentinel2_l1 = ee.ImageCollection(f'COPERNICUS/{collection}').filterBounds(roi).filterDate(start, end)
    else:
        sentinel2_l1 = ee.ImageCollection(f'COPERNICUS/{collection}').filterBounds(roi).filterDate(start, end).filter(ee.Filter.stringContains('PRODUCT_ID', tile))

    sentinel2_clouds = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(roi).filterDate(start, end)

    # Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
    return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
        'primary': sentinel2_l1,
        'secondary': sentinel2_clouds,
        'condition': ee.Filter.equals(**{
            'leftField': 'system:index',
            'rightField': 'system:index'
        })
    })).map(add_cloud_probability)

def add_cloud_probability(image : ee.Image) -> ee.Image:
    return image.addBands(ee.Image(image.get('s2cloudless')).select('probability'))

# L1
def to_rrs(image : ee.Image) -> ee.Image:
    rrs = image.divide(10_000)

    rrs = rrs.set('sza', image.get('MEAN_SOLAR_ZENITH_ANGLE'))
    rrs = rrs.set('saa', image.get('MEAN_SOLAR_AZIMUTH_ANGLE'))
    rrs = rrs.set('vza', get_mean_band_angle(image, 'ZENITH'))
    rrs = rrs.set('vaa', get_mean_band_angle(image, 'AZIMUTH'))

    raa = ee.Number(rrs.get('saa')).subtract(rrs.get('vaa')).abs()

    raa = ee.Algorithms.If(raa.gt(180), raa.subtract(360).abs(), raa)
    rrs = rrs.set('raa', raa)
    rrs = rrs.set('PRODUCT_ID', ee.String(ee.String(image.get('PRODUCT_ID')).split('L1C').get(0)))

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


# L2
def dask_spectrum_fitting(image : ee.Image) -> Tuple[ee.Image, List[str], dict]:
    am, glint_ave, bands = select_lut(image)
    
    rhos = select_sentinel2_bands(l1r_to_l2r(image, am))
    return rhos, bands, glint_ave

def select_lut(image : ee.Image, aot_skip_bands : List[str] = ['9', '10'], pencentil_idx : float = 0, nbands : int = 2) -> Tuple[dict, dict, List[str]]:
    results = {}
    percentiles = [0, 1, 5, 50, 95, 99, 100]
    prc = image.reduceRegion(reducer = ee.Reducer.percentile(percentiles), bestEffort = True, maxPixels = 1e13).getInfo()
    obands_rhot = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']
    prc_data = {p: {b: prc['{}_p{}'.format(b,p)] for b in obands_rhot} for p in percentiles}

    raa = image.get('raa').getInfo()
    vza = image.get('vza').getInfo()
    sza = image.get('sza').getInfo()
    sensor = 'S2A_MSI' if 'S2A' in image.get('PRODUCT_ID').getInfo() else 'S2B_MSI'
    
    uoz = 0.3
    uwv = 1.5
    pressure = 1013.25

    lutd = aerlut.import_luts(sensor = sensor)
    rsrd = shared.rsr_dict(sensor = sensor)[sensor]
    ttg = ac.gas_transmittance(sza, vza, pressure = pressure, uoz = uoz, uwv = uwv, rsr = rsrd['rsr'])
    luti = aerlut.import_rsky_luts(models=[1,2], lutbase='ACOLITE-RSKY-202102-82W', sensor=sensor)

    for lut in lutd:
        taua_arr = None
        rhot_arr = None
        taua_bands = []
        
        ## run through bands
        for b in rsrd['rsr_bands']:
            if b in aot_skip_bands: continue

            ret = lutd[lut]['rgi'][b]((pressure, lutd[lut]['ipd']['romix'], raa, vza, sza, lutd[lut]['meta']['tau']))
            rhot = np.asarray([prc_data[p]['B{}'.format(b)] for p in percentiles])
            rhot /= ttg['tt_gas'][b]
            taua = np.interp(rhot, ret, lutd[lut]['meta']['tau'])
            if taua_arr is None:
                rhot_arr = 1.0 * rhot
                taua_arr = 1.0 * taua
            else:
                rhot_arr = np.vstack((rhot_arr, rhot))
                taua_arr = np.vstack((taua_arr, taua))

            taua_bands.append(b)

        ## find aot value
        bidx = np.argsort(taua_arr[:, pencentil_idx])
        taua = np.nanmean(taua_arr[bidx[0: nbands], pencentil_idx])
        taua_std = np.nanstd(taua_arr[bidx[0: nbands], pencentil_idx])
        taua_cv = taua_std/taua
        taua, taua_std, taua_cv*100

        ## store results
        results[lut] = {'taua_bands': taua_bands, 'taua_arr': taua_arr, 'rhot_arr': rhot_arr,
                        'taua': taua, 'taua_std': taua_std, 'taua_cv': taua_cv,'bidx': bidx}

    ## select LUT and aot
    sel_lut = None
    sel_aot = None
    sel_val = np.inf
    sel_par = 'taua_cv'

    for lut in results:
        if results[lut][sel_par] < sel_val:
            sel_val = results[lut][sel_par] * 1.0
            sel_aot = results[lut]['taua'] * 1.0
            sel_lut = '{}'.format(lut)

    am = {}
    for par in lutd[sel_lut]['ipd']:
        am[par] = {b: lutd[sel_lut]['rgi'][b]((pressure, lutd[sel_lut]['ipd'][par], raa, vza, sza, sel_aot))
                    for b in rsrd['rsr_bands']}
    am.update({'tg' : ttg['tt_gas']})

    print(f'<{"-" * 100}>\nGeometry: {sza=}, {vza=}, {raa=}\nGases: {uwv=}, {uoz=}, {pressure=}\nLut: {sel_lut=}, {sel_aot=}\n<{"-" * 100}>')

    model = int(sel_lut[-1])
    glint_wind = 20
    glint_bands = ['11', '12']

    glint_dict = {b:luti[model]['rgi'][b]((raa, vza, sza, glint_wind, sel_aot)) for b in rsrd['rsr_bands']}
    glint_ave = {b: glint_dict[b]/((glint_dict[glint_bands[0]]+glint_dict[glint_bands[1]])/2) for b in glint_dict}

    return am, glint_ave, rsrd['rsr_bands']

def compute_pdark(image : ee.Image, option : str, settings : dict):
    obands_rhot = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']

    image_to_reduce = image.select(obands_rhot)
    pdark_by_band = {}
    if option == 'darkest':
        percentiles = [0]
        pdark_by_band = image_to_reduce.reduceRegion(reducer = ee.Reducer.percentile(percentiles), bestEffort = True, maxPixels = 1e13).getInfo()
    elif option == 'percentile':
        percentiles = [settings['dsf_percentile']]
        pdark_by_band = image_to_reduce.reduceRegion(reducer = ee.Reducer.percentile(percentiles), bestEffort = True, maxPixels = 1e13).getInfo()
    elif option == 'intercept':
        data = image_to_reduce.reduceRegion(reducer=ee.Reducer.toList(), bestEffort = True, maxPixels=1e13)
        indexes = np.arange(settings['dsf_intercept_pixels'])

        for band in obands_rhot:
            band_data = data.get(band)

            if band_data:
                values = ee.List(band_data).sort().slice(0, settings['dsf_intercept_pixels']).getInfo()
                slope, intercept, r, p, se = scipy.stats.linregress(indexes, values)
                pdark_by_band[band] = intercept
            else:
                pdark_by_band[band] = 0.0


    return pdark_by_band


def l1r_to_l2r(image : ee.Image, am : dict) -> ee.Image:
    l2r_rrs = ee.Image()

    romix = am['romix']
    dutott = am['dutott']
    astot = am['astot']
    tgas = am['tg']

    for band in romix:
        band_name = 'B' + band
        rhot_noatm = ee.Image().expression('(data / tg) - ppath', {'data' : image.select(band_name), 'tg' : tgas[band], 'ppath' : float(romix[band])}).rename(band_name)
        rhos = ee.Image().expression('(data) / (tdu + sa * data)', {'data' : rhot_noatm.select(band_name), 'tdu' : float(dutott[band]), 'sa' : float(astot[band])}).rename(band_name)
        rhos = mask_negative_reflectance(rhos, band_name)
        l2r_rrs = l2r_rrs.addBands(rhos)

    return l2r_rrs

def select_sentinel2_bands(image : ee.Image) -> ee.Image:
   return image.select(['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12'])


# Deglint
def deglint_alternative(image : ee.Image, bands : List[str], glint_ave : dict, glint_min : float = 0, glint_max : float = 0.08) -> ee.Image:
    deglinted = ee.Image()

    g1 = image.select('B11')
    g2 = image.select('B12')
    glint = (g1.add(g2)).divide(2).rename('glint')
    glintMask = glint.gt(glint_min).multiply(glint.lt(glint_max)).selfMask()
    glint = glint.mask(glintMask)
    glint = glint.unmask(0)

    for band in bands:
        band_name = 'B' + band
        if np.isinf(glint_ave[band]) or np.isnan(glint_ave[band]):
            rhos = image.select(band_name)
        else:
            rhos = ee.Image().expression('rhos - (rhog * {})'.format(glint_ave[band]), {'rhos': image.select(band_name), 'rhog': glint.select('glint')})
            
        rhos = mask_negative_reflectance(rhos, band_name)
        deglinted = deglinted.addBands(rhos)

    return deglinted


# Water Quality
def add_spm_nechad2016_665(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 342.10, 'C' : 0.19563, 'red' : image.select('B4') }).rename('SPM_Nechad2016_665'))

def add_spm_nechad2016_704(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 444.36, 'C' : 0.18753, 'red' : image.select('B5') }).rename('SPM_Nechad2016_704'))

def add_spm_nechad2016_739(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 1517.00, 'C' : 0.19736, 'red' : image.select('B6') }).rename('SPM_Nechad2016_739'))

def add_tur_nechad2016_665(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 366.14, 'C' : 0.19563, 'red' : image.select('B4') }).rename('TUR_Nechad2016_665'))

def add_tur_nechad2016_704(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 439.09, 'C' : 0.18753, 'red' : image.select('B5') }).rename('TUR_Nechad2016_704'))

def add_tur_nechad2016_739(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 1590.66, 'C' : 0.19736, 'red' : image.select('B6') }).rename('TUR_Nechad2016_739'))

def add_chl_oc2(image : ee.Image) -> ee.Image:
    A, B, C, D, E = 0.1977,-1.8117,1.9743,-2.5635,-0.7218 # TODO : interpolar B1 a las dimensiones de B2
    x = image.expression('log( x / y )', {'x' : image.select('B2'), 'y' : image.select('B3') }).rename('x')
    return image.addBands(image.expression('10 ** (A + B * x + C * (x**2) + D * (x**3) + E * (x**4) )', {'A' : A, 'B' : B, 'C' : C, 'D' : D, 'E' : E,
                                                                                                         'x' : x }).rename('chl_oc2'))

def add_chl_oc3(image : ee.Image) -> ee.Image:
    A, B, C, D, E = 0.2412,-2.0546,1.1776,-0.5538,-0.4570 # TODO : interpolar B1 a las dimensiones de B2
    x = image.expression('log( x / y )', {'x' : image.select('B2').max(image.select('B1')).rename('x'), 'y' : image.select('B3') }).rename('x')
    return image.addBands(image.expression('10 ** (A + B * x + C * (x**2) + D * (x**3) + E * (x**4) )', {'A' : A, 'B' : B, 'C' : C, 'D' : D, 'E' : E,
                                                                                                         'x' : x }).rename('chl_oc3'))

def add_chl_re_mishra(image : ee.Image) -> ee.Image:
    a, b, c = 14.039, 86.11, 194.325
    ndci = image.normalizedDifference(['B5', 'B4']).rename('ndci')
    return image.addBands(image.expression('a + b * ndci + c * ndci * ndci', {'a' : a, 'b' : b, 'c' : c, 'ndci' : ndci }).rename('chl_re_mishra'))

def add_ndwi(image : ee.Image) -> ee.Image:
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('ndwi')
    return image.addBands(ndwi)

def add_zred(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('log(n * pi * blue) / log(n * pi * red)', {'n' : 1_000, 
                                                                                       'pi' : float(np.pi), 
                                                                                       'blue' : image.select('B2'),
                                                                                       'red' : image.select('B4') }).rename('zred'))

def add_zgreen(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('log(n * pi * blue) / log(n * pi * green)', {'n' : 1_000, 
                                                                                       'pi' : float(np.pi), 
                                                                                       'blue' : image.select('B2'),
                                                                                       'green' : image.select('B3') }).rename('zgreen'))


# Bathymetry
def switching_model(green_model: ee.Image, red_model: ee.Image, green_coef: float = 3.5, red_coef: float = 2) -> ee.Image:
    null = -99_999
    
    # Convertir los coeficientes a ee.Image para poder usar operaciones de GEE
    green_coef_image = ee.Image(green_coef)
    red_coef_image = ee.Image(red_coef)

    # Calcular los coeficientes a y b
    a = green_coef_image.subtract(red_model).divide(green_coef_image.subtract(red_coef_image))
    b = ee.Image(1).subtract(a)

    # Calculando SDBw
    SDBw = a.multiply(red_model).add(b.multiply(green_model))

    # Iniciar la imagen de SDB con un valor representativo (usaremos -99_999 para representar NaN)
    SDB = ee.Image(null)

    # Aplicar las condiciones sobre SDB
    SDB = SDB.where(red_model.lt(red_coef_image), red_model)
    SDB = SDB.where(green_model.gt(green_coef_image).And(red_model.gt(red_coef_image)), green_model)
    SDB = SDB.where(green_model.lte(green_coef_image).And(red_model.gte(red_coef_image)), SDBw)

    # Asegurarse de que los valores negativos sean representados por null
    SDB = SDB.where(SDB.lt(0), ee.Image(null))

    # Aplicar máscara para los valores de null (estos se consideran no válidos)
    SDB = SDB.updateMask(SDB.neq(null))  # Usamos updateMask para que los píxeles con -99_999 no se muestren

    return SDB.rename('switching')


# Masking
def mask_water_by_NDWI(image : ee.Image, threshold : float = 0) -> ee.Image:
    ndwi = image.normalizedDifference(['B3', 'B8'])
    return image.updateMask(ndwi.gt(threshold))

def mask_non_water_by_SWIR1(image : ee.Image, threshold : float = 0.05) -> ee.Image:
    return image.updateMask( image.select('B11').lt(threshold) )

def mask_negative_reflectance(image : ee.Image, band : str) -> ee.Image:
    return image.updateMask(image.select(band).gte(0)).rename(band)

def mask_clouds_by_probability(image : ee.Image, threshold : int = 0) -> ee.Image:
    return image.updateMask(image.select('probability').lte(threshold))