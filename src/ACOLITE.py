import numpy as np
import scipy.stats
import ee
import os


from functools import partial
from datetime import datetime
from typing import List, Tuple, Optional
from acolite import ac, shared, aerlut
from acolite.acolite import settings as settings_manager



########################################################################
# Water Quality
########################################################################

def add_spm_nechad2016_665(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 342.10, 'C' : 0.19563, 'red' : image.select('B4') }).rename('SPM_Nechad2016_665'))

def add_spm_nechad2016_704(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 444.36, 'C' : 0.18753, 'red' : image.select('B5') }).rename('SPM_Nechad2016_704'))

def add_spm_nechad2016_740(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 1517.00, 'C' : 0.19736, 'red' : image.select('B6') }).rename('SPM_Nechad2016_739'))

def add_tur_nechad2016_665(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 366.14, 'C' : 0.19563, 'red' : image.select('B4') }).rename('TUR_Nechad2016_665'))

def add_tur_nechad2016_704(image : ee.Image) -> ee.Image:
    return image.addBands(image.expression('(A * red) / (1 - (red / C))', {'A' : 439.09, 'C' : 0.18753, 'red' : image.select('B5') }).rename('TUR_Nechad2016_704'))

def add_tur_nechad2016_740(image : ee.Image) -> ee.Image:
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

def add_rrs(image : ee.Image) -> ee.image:
    bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']

    for band in bands:
        outname = f'Rrs_{band}'
        image = image.addBands(image.select(band).divide(np.pi).rename(outname))

    return image


PRODUCTS = {
    'spm_nechad2016' : add_spm_nechad2016_665,
    'spm_nechad2016_704' : add_spm_nechad2016_704,
    'spm_nechad2016_740' : add_spm_nechad2016_740,
    'tur_nechad2016' : add_tur_nechad2016_665,
    'tur_nechad2016_704' : add_tur_nechad2016_704,
    'tur_nechad2016_740' : add_tur_nechad2016_740,
    'chl_oc2' : add_chl_oc2,
    'chl_oc3' : add_chl_oc3,
    'chl_re_mishra' : add_chl_re_mishra,
    'zred' : add_zred,
    'zgreen' : add_zgreen,
    'Rrs_*' : add_rrs
}


########################################################################



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


def run_acolite(images : ee.ImageCollection, settings : str) -> Tuple[ee.ImageCollection, dict]:
    settings = read_settings(settings)

    images = prepare_l1_rrs(images)
    images, settings = correct_l1(images.toList(images.size()), images.size().getInfo(), settings)

    return images, settings


def read_settings(settings : str) -> dict:
    return settings_manager.parse('S2A_MSI', settings = settings)

def prepare_l1_rrs(images : ee.ImageCollection) -> ee.ImageCollection:
    return images.map(select_sentinel2_bands).map(to_rrs)

def correct_l1(images : ee.List, size : int, settings : dict) -> Tuple[ee.ImageCollection, dict]:
    corrected_images = []

    if settings['aerosol_correction'] == 'dark_spectrum':
        for index in range(size):
            rhos, bands, glint_params = dask_spectrum_fitting(ee.Image(images.get(index)), settings)
    
            if settings['dsf_residual_glint_correction']:
                if settings['dsf_residual_glint_correction_method'] == 'alternative':
                    rhos = deglint_alternative(rhos, bands, glint_params)

            corrected_images.append(rhos)
        
    return ee.ImageCollection.fromImages(corrected_images), settings

def compute_water_quality(images, settings) -> ee.ImageCollection:
    if settings['l2w_parameters']:
        if isinstance(settings['l2w_parameters'], str):
            settings['l2w_parameters'] = [settings['l2w_parameters']]

        mask_non_water_by_SWIR1_modified = partial(mask_non_water_by_SWIR1, threshold = settings['l2w_mask_threshold'])
        images = images.map(mask_non_water_by_SWIR1_modified)

        for product in settings['l2w_parameters']:
            images = images.map(PRODUCTS[product])

    return images



def get_ancillary_data(image, settings : dict) -> dict:
    prepare_earthdata_credentials(settings)
    iso_date, lon, lat = prepare_query(image)

    anc = ac.ancillary.get(iso_date, lon, lat)

    for data, default in [('uoz', 'uoz_default'), ('uwv', 'uwv_default'), 
                          ('wind', 'wind_default'), ('pressure', 'pressure_default')]:
        settings[data] = anc.get(data, settings.get(default)) 
    
    return settings

def prepare_query(image):
    coords = image.geometry().centroid().coordinates().getInfo()
    iso_date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd HH:mm:ss').getInfo()

    lon, lat = coords
    return iso_date,lon,lat

def prepare_earthdata_credentials(settings):
    for k in ['EARTHDATA_u', 'EARTHDATA_p']:
        kv = settings[k] if k in settings else ac.config[k]
        if len(kv) == 0: continue
        os.environ[k] = kv



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

    rrs = rrs.set('system:time_start', image.get('system:time_start'))

    return rrs

def resample_to_10m(image : ee.Image) -> ee.Image:
    return image.resample('bilinear').reproject(crs = image.select('B2').projection().crs(),
                                                scale=10)

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
def dask_spectrum_fitting(image : ee.Image, settings : dict) -> Tuple[ee.Image, List[str], dict]:
    if settings['ancillary_data']:
        settings = get_ancillary_data(image, settings)
    else:
        for data, default in [('uoz', 'uoz_default'), ('uwv', 'uwv_default'), ('wind', 'wind_default'), ('pressure', 'pressure_default')]:
            settings[data] = settings.get(default)

    am, glint_ave, bands = select_lut(image, settings)
    rhos = select_sentinel2_bands(l1r_to_l2r(image, am))

    return rhos, bands, glint_ave

def select_lut(image : ee.Image, settings : dict, aot_skip_bands : List[str] = ['9', '10', '11', '12']) -> Tuple[dict, dict, List[str]]:
    results = {}
    
    pdark = compute_pdark(image, settings)

    raa = image.get('raa').getInfo()
    vza = image.get('vza').getInfo()
    sza = image.get('sza').getInfo()

    sensor = 'S2A_MSI' if 'S2A' in image.get('PRODUCT_ID').getInfo() else 'S2B_MSI'
    
    uoz = settings['uoz']
    uwv = settings['uwv']
    pressure = settings['pressure']
    nbands = settings['dsf_nbands']

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

            rhot = np.asarray([pdark['B{}'.format(b)]])
            
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
        bidx = np.argsort(taua_arr[:, 0])
        taua = np.nanmean(taua_arr[bidx[0: nbands], 0])
        taua_std = np.nanstd(taua_arr[bidx[0: nbands], 0])
        taua_cv = taua_std/taua
        taua, taua_std, taua_cv*100

        ## store results
        results[lut] = {'taua_bands': taua_bands, 'taua_arr': taua_arr, 'rhot_arr': rhot_arr,
                        'taua': taua, 'taua_std': taua_std, 'taua_cv': taua_cv,'bidx': bidx}

    print(f'{results=}')
    
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

    print_summary(image, pdark, raa, vza, sza, uoz, uwv, pressure, sel_lut, sel_aot)

    model = int(sel_lut[-1])
    glint_wind = 20
    glint_bands = ['11', '12']

    glint_dict = {b:luti[model]['rgi'][b]((raa, vza, sza, glint_wind, sel_aot)) for b in rsrd['rsr_bands']}
    glint_ave = {b: glint_dict[b]/((glint_dict[glint_bands[0]]+glint_dict[glint_bands[1]])/2) for b in glint_dict}

    return am, glint_ave, rsrd['rsr_bands']

def print_summary(image, pdark, raa, vza, sza, uoz, uwv, pressure, sel_lut, sel_aot):
    timestamp = image.get('system:time_start').getInfo()
    iso_date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd HH:mm:ss').getInfo()

    print('date,sza,vza,raa,uoz, uwv, pressure,1 darkest,2 darkest,3 darkest,4 darkest,5 darkest,6 darkest,7 darkest,8 darkest,8A darkest,LUT,aot')
    values = [iso_date, f'{sza:.3f}', f'{vza:.3f}', f'{raa:.3f}', f'{uoz:.3f}', f'{uwv:.3f}', f'{pressure:.3f}', 
              *[f"{pdark[f'B{band}']:.3f}" for band in [1, 2, 3, 4, 5, 6, 7, 8, '8A']], sel_lut, f'{sel_aot:.3f}']
    print(f'{values}')

def compute_pdark(image : ee.Image, settings : dict):
    obands_rhot = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']

    image_to_reduce = image.updateMask(image.gt(0))

    pdark_by_band = {}
    indexes = np.arange(settings['dsf_intercept_pixels'])

    for band in obands_rhot:
        if settings['dsf_spectrum_option'] == 'darkest':
            band_data = image_to_reduce.select(band).reduceRegion(reducer = ee.Reducer.percentile([0]), 
                                                     bestEffort = True, scale = 10, maxPixels = 1e8)
            
            if band_data:
                pdark_by_band[band] = band_data.getInfo()[band]
            else:
                pdark_by_band[band] = 0.0

        elif settings['dsf_spectrum_option'] == 'percentile':
            band_data = image_to_reduce.select(band).reduceRegion(reducer = ee.Reducer.percentile([settings['dsf_percentile']]), 
                                                     bestEffort = True, scale = 10, maxPixels = 1e8)
            
            if band_data:
                pdark_by_band[band] = band_data.getInfo()[band]
            else:
                pdark_by_band[band] = 0.0
        elif settings['dsf_spectrum_option'] == 'intercept':
            data = image_to_reduce.select(band).reduceRegion(reducer = ee.Reducer.toList(), scale = 30, bestEffort = True, maxPixels = 1e8)
            band_data = data.get(band)

            if band_data:
                values = ee.List(band_data).sort().slice(0, settings['dsf_intercept_pixels']).getInfo()
                slope, intercept, r, p, se = scipy.stats.linregress(indexes, values)
                pdark_by_band[band] = intercept
            else:
                pdark_by_band[band] = 0.0

    # if settings['dsf_spectrum_option'] == 'darkest':
    #     pdark_by_band = image_to_reduce.select(obands_rhot).reduceRegion(reducer = ee.Reducer.percentile([0]), 
    #                                                  bestEffort = True, scale = 10, maxPixels = 1e8).getInfo()
    #     print(pdark_by_band)
    # elif settings['dsf_spectrum_option'] == 'percentile':
    #     pdark_by_band = image_to_reduce.select(obands_rhot).reduceRegion(reducer = ee.Reducer.percentile([settings['dsf_percentile']]), 
    #                                                  bestEffort = True, scale = 10, maxPixels = 1e8).getInfo()
    # elif settings['dsf_spectrum_option'] == 'intercept':
    #     indexes = np.arange(settings['dsf_intercept_pixels'])

    #     for band in obands_rhot:
    #         data = image_to_reduce.select(band).reduceRegion(reducer = ee.Reducer.toList(), scale = 30, bestEffort = True, maxPixels = 1e8)
    #         band_data = data.get(band)

    #         if band_data:
    #             values = ee.List(band_data).sort().slice(0, settings['dsf_intercept_pixels']).getInfo()
    #             slope, intercept, r, p, se = scipy.stats.linregress(indexes, values)
    #             pdark_by_band[band] = intercept
    #         else:
    #             pdark_by_band[band] = 0.0


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