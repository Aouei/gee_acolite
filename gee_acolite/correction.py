import numpy as np
import scipy.stats
import ee
import os


from typing import List, Tuple
from types import ModuleType
from functools import partial

from gee_acolite.utils.l1_convert import l1_to_rrs
from gee_acolite.utils.masks import mask_negative_reflectance
from gee_acolite.water_quality import compute_water_bands


class ACOLITE(object):
    def __init__(self, acolite: ModuleType, settings: str | dict) -> None:
        self.acolite = acolite
        self.settings = self.__load_settings(settings)

    def __load_settings(self, settings: str | dict):
        # return self.acolite.acolite.settings.load(settings)
        return self.acolite.acolite.settings.parse('S2A_MSI', settings = settings)
    
    def correct(self, images : ee.ImageCollection) -> Tuple[ee.ImageCollection, dict]:
        images = l1_to_rrs(images, self.settings.get('s2_target_res', 10))
        images, settings = self.l1_to_l2(images.toList(images.size()), images.size().getInfo(), self.settings)

        return images, settings
    

    def l1_to_l2(self, images : ee.List, size : int, settings : dict) -> Tuple[ee.ImageCollection, dict]:
        corrected_images = []

        if settings['aerosol_correction'] == 'dark_spectrum':
            for index in range(size):
                rhos, bands, glint_params = self.dask_spectrum_fitting(ee.Image(images.get(index)), settings)
        
                if settings['dsf_residual_glint_correction'] and settings['dsf_residual_glint_correction_method'] == 'alternative':
                    rhos = self.deglint_alternative(rhos, 
                                                    bands, 
                                                    glint_params,
                                                    glint_max=float(settings.get('glint_mask_rhos_threshold', 0.05)))

                rhos = rhos.copyProperties(ee.Image(images.get(index)))
                rhos = rhos.set('system:time_start', ee.Image(images.get(index)).get('system:time_start'))

                corrected_images.append(rhos)
            
        corrected_images = ee.ImageCollection.fromImages(corrected_images)

        if settings['l2w_parameters']:
            corrected_images = corrected_images.map(partial(compute_water_bands, settings=settings))
            
        return corrected_images, settings
    
    def dask_spectrum_fitting(self, image : ee.Image, settings : dict) -> Tuple[ee.Image, List[str], dict]:
        if settings.get('ancillary_data', False):
            settings = self.get_ancillary_data(image, settings)
        else:
            for data, default in [(key, f'{key}_default') for key in ['uoz', 'uwv', 'wind', 'pressure']]:
                settings[data] = settings.get(default)

        am, glint_ave, bands = self.select_lut(image, settings)
        rhos = self.compute_rhos(image, am)

        return rhos, bands, glint_ave
    
    def select_lut(self, image : ee.Image, settings : dict, aot_skip_bands : List[str] = ['9', '10', '11', '12']) -> Tuple[dict, dict, List[str]]:
        results = {}
        
        pdark = self.compute_pdark(image, settings)

        raa = image.get('raa').getInfo()
        vza = image.get('vza').getInfo()
        sza = image.get('sza').getInfo()

        sensor = 'S2A_MSI' if 'S2A' in image.get('PRODUCT_ID').getInfo() else 'S2B_MSI'
        
        uoz = settings['uoz']
        uwv = settings['uwv']
        pressure = settings['pressure']
        nbands = settings['dsf_nbands']

        lutd = self.acolite.aerlut.import_luts(sensor = sensor)
        rsrd = self.acolite.shared.rsr_dict(sensor = sensor)[sensor]
        ttg = self.acolite.ac.gas_transmittance(sza, vza, pressure = pressure, uoz = uoz, uwv = uwv, rsr = rsrd['rsr'])
        luti = self.acolite.aerlut.import_rsky_luts(models=[1,2], lutbase='ACOLITE-RSKY-202102-82W', sensor=sensor)

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

        model = int(sel_lut[-1])
        glint_wind = 20
        glint_bands = ['11', '12']

        glint_dict = {b:luti[model]['rgi'][b]((raa, vza, sza, glint_wind, sel_aot)) for b in rsrd['rsr_bands']}
        glint_ave = {b: glint_dict[b]/((glint_dict[glint_bands[0]]+glint_dict[glint_bands[1]])/2) for b in glint_dict}

        return am, glint_ave, rsrd['rsr_bands']
    
    def compute_pdark(self, image : ee.Image, settings : dict):
        obands_rhot = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']

        image_to_reduce = image.updateMask(image.gt(0))

        pdark_by_band = {}
        indexes = np.arange(settings['dsf_intercept_pixels'])

        for band in obands_rhot:
            if settings.get('dsf_spectrum_option', 'darkest') == 'darkest':
                band_data = image_to_reduce.select(band).reduceRegion(reducer = ee.Reducer.percentile([0]), 
                                                        bestEffort = True, scale = 10, maxPixels = 1e8)
                
                if band_data:
                    pdark_by_band[band] = band_data.getInfo()[band]
                else:
                    pdark_by_band[band] = 0.0

            elif settings.get('dsf_spectrum_option', 'darkest') == 'percentile':
                band_data = image_to_reduce.select(band).reduceRegion(reducer = ee.Reducer.percentile([settings['dsf_percentile']]), 
                                                        bestEffort = True, scale = 10, maxPixels = 1e8)
                
                if band_data:
                    pdark_by_band[band] = band_data.getInfo()[band]
                else:
                    pdark_by_band[band] = 0.0
            elif settings.get('dsf_spectrum_option', 'darkest') == 'intercept':
                data = image_to_reduce.select(band).reduceRegion(reducer = ee.Reducer.toList(), scale = 30, bestEffort = True, maxPixels = 1e8)
                band_data = data.get(band)

                if band_data:
                    values = ee.List(band_data).sort().slice(0, settings['dsf_intercept_pixels']).getInfo()
                    slope, intercept, r, p, se = scipy.stats.linregress(indexes, values)
                    pdark_by_band[band] = intercept
                else:
                    pdark_by_band[band] = 0.0

        return pdark_by_band
    
    def compute_rhos(self, image : ee.Image, am : dict) -> ee.Image:
        l2r_rrs = ee.Image().select([])

        romix = am['romix']
        dutott = am['dutott']
        astot = am['astot']
        tgas = am['tg']

        for band in romix:
            band_name = 'B' + band
            rhot_noatm = ee.Image().expression('(data / tg) - ppath', {'data' : image.select(band_name), 'tg' : tgas[band], 'ppath' : float(romix[band])}).rename(band_name)
            rhos = ee.Image().expression('(data) / (tdu + sa * data)', {'data' : rhot_noatm.select(band_name), 'tdu' : float(dutott[band]), 'sa' : float(astot[band])}).rename(band_name)
            rhos = mask_negative_reflectance(rhos, band_name)
            l2r_rrs = l2r_rrs.addBands(image.select(band_name).rename(f'rhot_{band_name}').toFloat())
            l2r_rrs = l2r_rrs.addBands(rhos.rename(f'rhos_{band_name}').toFloat())

        return l2r_rrs


    def get_ancillary_data(self, image: ee.Image, settings : dict) -> dict:
        settings = self.prepare_earthdata_credentials(settings)
        iso_date, lon, lat = self.prepare_query(image)

        anc = self.acolite.ac.ancillary.get(iso_date, lon, lat)

        for data, default in [('uoz', 'uoz_default'), ('uwv', 'uwv_default'), 
                            ('wind', 'wind_default'), ('pressure', 'pressure_default')]:
            settings[data] = anc.get(data, settings.get(default)) 
        
        return settings

    def prepare_query(self, image: ee.Image):
        coords = image.geometry().centroid().coordinates().getInfo()
        iso_date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd HH:mm:ss').getInfo()

        lon, lat = coords
        return iso_date,lon,lat

    def prepare_earthdata_credentials(self, settings: dict) -> dict:
        for k in ['EARTHDATA_u', 'EARTHDATA_p']:
            kv = settings[k] if k in settings else self.acolite.ac.config[k]
            if len(kv) == 0: continue
            os.environ[k] = kv
        
        return settings


    def deglint_alternative(self, image : ee.Image, bands : List[str], 
                            glint_ave : dict, glint_min : float = 0, glint_max : float = 0.08) -> ee.Image:
        """
        Alternative glint correction method based on ACOLITE's acolite_l2r.py implementation.
        
        This method:
        1. Uses reference SWIR bands (B11, B12) to estimate observed glint
        2. Computes average modeled surface reflectance (glint_ave) for reference bands
        3. For each band, scales the observed glint by the ratio of:
           - Modeled surface reflectance for current band
           - Average modeled surface reflectance of reference bands
        4. Subtracts the scaled glint from each band's rhos
        
        Parameters:
        - image: Image with rhos bands
        - bands: List of band numbers (as strings)
        - glint_ave: Dict with modeled surface reflectance ratio per band
        - glint_min: Minimum threshold for glint mask (default: 0)
        - glint_max: Maximum threshold for glint mask (glint_mask_rhos_threshold)
        """
        
        # Start with a copy of the original image to preserve all bands
        deglinted = image
        
        # Reference bands for glint estimation (SWIR bands: B11=1610nm, B12=2190nm)
        # These bands are sensitive to sun glint but have minimal water-leaving radiance
        glint_ref_bands = ['rhos_B11', 'rhos_B12']
        
        # Step 1: Compute observed glint reference (gc_ref_mean in ACOLITE)
        # Average of reference bands gives the observed glint signal
        rhos_b11 = image.select('rhos_B11')
        rhos_b12 = image.select('rhos_B12')
        gc_ref_mean = (rhos_b11.add(rhos_b12)).divide(2).rename('gc_ref_mean')
        
        # Step 2: Compute average modeled surface reflectance for reference bands (gc_sur_mean in ACOLITE)
        # This is the average of glint_ave values for B11 and B12
        gc_sur_mean = (glint_ave['11'] + glint_ave['12']) / 2.0
        
        # Step 3: Create glint mask (gc_sub in ACOLITE)
        # Only apply correction where observed glint is below threshold and positive
        glint_mask = gc_ref_mean.gt(glint_min).And(gc_ref_mean.lt(glint_max))
        
        # Step 4: Apply band-specific glint correction
        for band in bands:
            band_name = 'rhos_B' + band
            
            # Skip if modeled surface reflectance is invalid
            if np.isinf(glint_ave[band]) or np.isnan(glint_ave[band]):
                continue
            
            # Compute current band glint (cur_rhog in ACOLITE):
            # cur_rhog = gc_ref_mean * (surf_current_band / gc_sur_mean)
            # 
            # This scales the observed glint by the ratio of:
            # - Modeled surface reflectance for current band (glint_ave[band])
            # - Average modeled surface reflectance of reference bands (gc_sur_mean)
            #
            # The ratio accounts for spectral variation in surface reflectance
            glint_ratio = glint_ave[band] / gc_sur_mean
            cur_rhog = gc_ref_mean.multiply(glint_ratio).rename('cur_rhog')
            
            # Mask the glint correction to valid pixels
            cur_rhog = cur_rhog.updateMask(glint_mask)
            
            # Apply glint correction: rhos_corrected = rhos_original - glint
            rhos_corrected = image.select(band_name).subtract(cur_rhog)
            
            # Mask negative values (can occur in dark pixels or over-correction)
            rhos_corrected = mask_negative_reflectance(rhos_corrected, band_name)
            
            # Replace the band in the output image (overwrite=True)
            deglinted = deglinted.addBands(rhos_corrected, overwrite=True)
        
        # Optional: Write glint mean for visualization/validation
        deglinted = deglinted.addBands(gc_ref_mean.rename('glint_mean'))
        
        return deglinted