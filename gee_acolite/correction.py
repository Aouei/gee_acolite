"""
Atmospheric correction using ACOLITE Dark Spectrum Fitting.

This module implements the ACOLITE atmospheric correction method adapted for
Google Earth Engine workflows with Sentinel-2 imagery. It provides dark spectrum
fitting for aerosol optical thickness (AOT) estimation and atmospheric correction.
"""
import numpy as np
import scipy.stats
import ee
import os
import warnings


from typing import List, Tuple
from types import ModuleType
from functools import partial

from gee_acolite.utils.l1_convert import l1_to_rrs
from gee_acolite.utils.masks import mask_negative_reflectance
from gee_acolite.water_quality import compute_water_bands


class ACOLITE(object):
    """
    ACOLITE atmospheric correction for Google Earth Engine.
    
    This class implements the ACOLITE Dark Spectrum Fitting (DSF) atmospheric
    correction method optimized for Google Earth Engine with Sentinel-2 imagery.
    
    Parameters
    ----------
    acolite : ModuleType
        ACOLITE module imported from the ACOLITE package.
    settings : str or dict
        Path to settings file or dictionary with processing settings.
    
    Attributes
    ----------
    acolite : ModuleType
        Reference to ACOLITE module.
    settings : dict
        Parsed processing settings.
    
    Examples
    --------
    >>> import acolite as ac
    >>> from gee_acolite import ACOLITE
    >>> ac_gee = ACOLITE(ac, 'config/settings.txt')
    >>> corrected_images, settings = ac_gee.correct(image_collection)
    """
    
    def __init__(self, acolite: ModuleType, settings: str | dict) -> None:
        self.acolite = acolite
        self.settings = self.__load_settings(settings)

    def __load_settings(self, settings: str | dict):
        """
        Load and parse ACOLITE settings.
        
        Parameters
        ----------
        settings : str or dict
            Path to settings file or dictionary with settings.
        
        Returns
        -------
        dict
            Parsed settings dictionary.
        """
        settings_api = self.acolite.acolite.settings

        # ACOLITE >= 2025.01 no longer merges config/defaults.txt in parse(),
        # so defaults (e.g. uoz_default) are filled explicitly here.
        merged = settings_api.load('S2A_MSI')
        user_settings = settings_api.read(settings) if isinstance(settings, str) else settings
        merged.update(user_settings or {})

        return settings_api.parse('S2A_MSI', settings = merged)
    
    def correct(self, images : ee.ImageCollection) -> Tuple[ee.ImageCollection, dict]:
        """
        Apply atmospheric correction to image collection.
        
        Main entry point for atmospheric correction processing. Converts L1C
        top-of-atmosphere (TOA) reflectance to surface reflectance using the
        ACOLITE Dark Spectrum Fitting method.
        
        Parameters
        ----------
        images : ee.ImageCollection
            Collection of Sentinel-2 L1C images.
        
        Returns
        -------
        corrected_images : ee.ImageCollection
            Atmospherically corrected images with surface reflectance bands.
        settings : dict
            Processing settings used for correction.

        Notes
        -----
        Settings read here: ``s2_target_res`` (default 10) and
        ``s2_resampling_method`` (``'nearest'`` (default) or ``'bilinear'``),
        the interpolation used to bring the 20 m / 60 m bands to the target grid.
        """
        images = l1_to_rrs(images,
                           self.settings.get('s2_target_res', 10),
                           resampling = self.settings.get('s2_resampling_method', 'nearest'))
        images, settings = self.l1_to_l2(images.toList(images.size()), images.size().getInfo(), self.settings)

        return images, settings
    

    def l1_to_l2(self, images : ee.List, size : int, settings : dict) -> Tuple[ee.ImageCollection, dict]:
        """
        Convert L1 TOA reflectance to L2 surface reflectance.
        
        Processes each image in the collection through atmospheric correction
        and optionally applies residual glint correction and water quality
        parameter computation.
        
        Parameters
        ----------
        images : ee.List
            List of ee.Image objects (L1C TOA reflectance).
        size : int
            Number of images in the list.
        settings : dict
            Processing settings including correction parameters.
        
        Returns
        -------
        corrected_images : ee.ImageCollection
            Collection of atmospherically corrected images.
        settings : dict
            Processing settings used.
        """
        corrected_images = []

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
        """
        Perform dark spectrum fitting atmospheric correction.
        
        Main workflow for dark spectrum fitting (DSF). Retrieves ancillary data,
        selects optimal atmospheric model (LUT), estimates AOT, and computes
        surface reflectance.
        
        Parameters
        ----------
        image : ee.Image
            Input image with TOA reflectance.
        settings : dict
            Processing settings.
        
        Returns
        -------
        rhos : ee.Image
            Surface reflectance image.
        bands : list of str
            List of band names processed.
        glint_ave : dict
            Glint correction parameters per band.
        """
        if settings.get('ancillary_data', False):
            settings = self.get_ancillary_data(image, settings)
        else:
            for data, default in [(key, f'{key}_default') for key in ['uoz', 'uwv', 'wind', 'pressure']]:
                settings[data] = settings.get(default)

        # Check if fixed AOT and LUT are provided
        if settings.get('dsf_fixed_aot') is not None and settings.get('dsf_fixed_lut') is not None:
            # Use fixed AOT and LUT (bypass dark spectrum fitting)
            am, glint_ave, bands = self.compute_correction_with_fixed_aot(
                image, 
                float(settings['dsf_fixed_aot']), 
                settings['dsf_fixed_lut'], 
                settings
            )
        else:
            # Normal dark spectrum fitting workflow
            am, glint_ave, bands = self.select_lut(image, settings)
        
        rhos = self.compute_rhos(image, am)

        return rhos, bands, glint_ave
    
    def estimate_aot_per_lut(self, pdark: dict, lutd: dict, rsrd: dict, ttg: dict, 
                             geometry: dict, settings: dict, 
                             aot_skip_bands: List[str] = ['9', '10', '11', '12']) -> dict:
        """
        Estimate aerosol optical thickness (AOT) for each LUT model.
        
        Uses dark spectrum fitting to estimate AOT at 550nm for each atmospheric
        model in the LUT dictionary. The method finds AOT values that best match
        observed dark spectrum reflectance with modeled path reflectance.

        This follows ACOLITE's fixed AOT estimation:

        * a band whose (gas corrected) dark spectrum value falls outside the range
          modeled by the LUT gets a NaN AOT and is dropped from the ranking, unless
          ``dsf_allow_lut_boundaries`` is set, in which case it is clamped to the
          LUT AOT limits (gee_acolite <= 1.2.x behaviour);
        * the AOT is taken from the lowest-AOT bands according to ``dsf_aot_compute``;
        * if no band yields a valid AOT the AOT is set to 0.01.

        Parameters
        ----------
        pdark : dict
            Dark spectrum values per band (e.g., {'B1': 0.05, 'B2': 0.04, ...}).
        lutd : dict
            Look-up table dictionary with atmospheric models.
        rsrd : dict
            Relative spectral response dictionary for the sensor.
        ttg : dict
            Gas transmittance values per band.
        geometry : dict
            Viewing geometry with keys 'raa', 'vza', 'sza', 'pressure'.
        settings : dict
            Processing settings. Keys read: 'dsf_nbands', 'dsf_aot_compute'
            ('min' (default), 'mean' or 'median'; mean/median use the 'dsf_nbands'
            lowest bands) and 'dsf_allow_lut_boundaries' (default False).
        aot_skip_bands : list of str, optional
            Band numbers to skip in AOT estimation (default: ['9', '10', '11', '12']).
        
        Returns
        -------
        results : dict
            Dictionary with AOT estimation results per LUT model.
            Each entry contains: 'taua', 'taua_std', 'taua_cv', 'taua_bands',
            'taua_arr', 'rhot_arr', 'bidx'.
        """
        results = {}
        nbands = settings['dsf_nbands']
        aot_compute = settings.get('dsf_aot_compute', 'min')

        # ACOLITE: left, right = nan, nan unless dsf_allow_lut_boundaries
        left = right = np.nan
        if settings.get('dsf_allow_lut_boundaries', False):
            left = right = None

        raa = geometry['raa']
        vza = geometry['vza']
        sza = geometry['sza']
        pressure = geometry['pressure']

        for lut in lutd:
            taua_arr = None
            rhot_arr = None
            taua_bands = []
            
            # Run through bands to estimate AOT
            for b in rsrd['rsr_bands']:
                if b in aot_skip_bands: 
                    continue

                # Get path reflectance from LUT for this band
                ret = lutd[lut]['rgi'][b]((pressure, lutd[lut]['ipd']['romix'], 
                                          raa, vza, sza, lutd[lut]['meta']['tau']))

                # Dark spectrum value for this band
                rhot = np.asarray([pdark['B{}'.format(b)]], dtype=float)

                # Gas correction
                rhot /= ttg['tt_gas'][b]

                # Interpolate AOT from observed rhot (NaN outside the LUT range by default)
                taua = np.interp(rhot, ret, lutd[lut]['meta']['tau'], left=left, right=right)
                
                if taua_arr is None:
                    rhot_arr = 1.0 * rhot
                    taua_arr = 1.0 * taua
                else:
                    rhot_arr = np.vstack((rhot_arr, rhot))
                    taua_arr = np.vstack((taua_arr, taua))

                taua_bands.append(b)

            # Rank bands by AOT (np.argsort puts NaN last)
            bidx = np.argsort(taua_arr[:, 0])
            lowest = taua_arr[bidx[0: nbands], 0]

            # Aggregate AOT from the lowest bands
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                if aot_compute == 'mean':
                    taua = np.nanmean(lowest)
                elif aot_compute == 'median':
                    taua = np.nanmedian(lowest)
                else:
                    taua = taua_arr[bidx[0], 0]
                taua_std = np.nanstd(lowest)

            # ACOLITE fixed AOT fallback when no band gives a valid AOT
            if not np.isfinite(taua):
                taua = 0.01
                taua_std = 0.0

            taua_cv = taua_std / taua if taua > 0 else np.inf

            # Store results for this LUT
            results[lut] = {
                'taua_bands': taua_bands, 
                'taua_arr': taua_arr, 
                'rhot_arr': rhot_arr,
                'taua': taua, 
                'taua_std': taua_std, 
                'taua_cv': taua_cv,
                'bidx': bidx
            }
        
        return results
    
    def select_best_model(self, results: dict, lutd: dict, geometry: dict, 
                         settings: dict) -> Tuple[str, float, str, float]:
        """
        Select the best atmospheric model from AOT estimation results.
        
        Evaluates multiple atmospheric models and selects the one that best
        fits the observed data based on the specified selection criterion
        (e.g., minimum RMSD, minimum delta tau, or coefficient of variation).
        
        Parameters
        ----------
        results : dict
            AOT estimation results per LUT from estimate_aot_per_lut.
        lutd : dict
            Look-up table dictionary with atmospheric models.
        geometry : dict
            Viewing geometry with keys 'raa', 'vza', 'sza', 'pressure'.
        settings : dict
            Processing settings including 'dsf_model_selection' and 'dsf_nbands_fit'.
        
        Returns
        -------
        sel_lut : str
            Selected LUT name (e.g., 'ACOLITE-LUT-202110-MOD1').
        sel_aot : float
            Selected AOT value at 550nm.
        sel_par : str
            Selection parameter name used ('rmsd', 'dtau', or 'taua_cv').
        sel_val : float
            Value of the selection parameter for the chosen model.
        """
        dsf_model_selection = settings.get('dsf_model_selection', 'min_drmsd')
        dsf_nbands_fit = settings.get('dsf_nbands_fit', 2)
        
        pressure = geometry['pressure']
        raa = geometry['raa']
        vza = geometry['vza']
        sza = geometry['sza']
        
        if dsf_model_selection == 'min_drmsd':
            # RMSD validation: compare predictions vs observations
            for lut in results:
                fit_band_indices = results[lut]['bidx'][0:dsf_nbands_fit]
                
                rmsd_values = []
                for fit_idx in fit_band_indices:
                    band = results[lut]['taua_bands'][fit_idx]
                    
                    # Observed rhot (gas corrected)
                    rhot_obs = results[lut]['rhot_arr'][fit_idx, 0]
                    
                    # Modeled rhot using estimated AOT
                    rhot_model = lutd[lut]['rgi'][band]((pressure, lutd[lut]['ipd']['romix'], 
                                                         raa, vza, sza, results[lut]['taua']))
                    
                    # Squared difference
                    rmsd_values.append((rhot_obs - rhot_model) ** 2)
                
                # Compute RMSD (a non-finite value, e.g. from a band without valid
                # dark spectrum, can never win the model selection)
                rmsd = np.sqrt(np.mean(rmsd_values))
                results[lut]['rmsd'] = rmsd if np.isfinite(rmsd) else np.inf
            
            sel_par = 'rmsd'
            
        elif dsf_model_selection == 'min_dtau':
            # Minimum delta tau between two darkest bands
            for lut in results:
                if len(results[lut]['taua_arr']) >= 2:
                    dtau = np.abs(results[lut]['taua_arr'][results[lut]['bidx'][0], 0] - 
                                  results[lut]['taua_arr'][results[lut]['bidx'][1], 0])
                    results[lut]['dtau'] = dtau
                else:
                    results[lut]['dtau'] = np.inf
            
            sel_par = 'dtau'
            
        else:
            # Fallback: coefficient of variation
            sel_par = 'taua_cv'
        
        # Select LUT with minimum selection parameter
        sel_lut = None
        sel_aot = None
        sel_val = np.inf

        for lut in results:
            if results[lut][sel_par] < sel_val:
                sel_val = results[lut][sel_par] * 1.0
                sel_aot = results[lut]['taua'] * 1.0
                sel_lut = '{}'.format(lut)

        # No model has a finite selection parameter: keep the first model
        # (ACOLITE also keeps the first LUT as its initial selection)
        if sel_lut is None:
            sel_lut = '{}'.format(next(iter(results)))
            sel_aot = results[sel_lut]['taua'] * 1.0

        return sel_lut, sel_aot, sel_par, sel_val
    
    def select_lut(self, image : ee.Image, settings : dict, aot_skip_bands : List[str] = ['9', '10', '11', '12']) -> Tuple[dict, dict, List[str]]:
        """
        Select optimal LUT and compute atmospheric correction parameters.
        
        Main orchestration function for the dark spectrum fitting workflow:
        
        1. Extracts dark spectrum from the image
        2. Estimates AOT for each atmospheric model
        3. Selects the best model based on validation criterion
        4. Computes atmospheric correction parameters (path reflectance, transmittance, spherical albedo, gas transmittance)
        5. Computes glint correction parameters
        
        Parameters
        ----------
        image : ee.Image
            Input image with TOA reflectance and geometry metadata.
        settings : dict
            Processing settings.
        aot_skip_bands : list of str, optional
            Band numbers to skip in AOT estimation (default: ['9', '10', '11', '12']).
        
        Returns
        -------
        am : dict
            Atmospheric correction parameters with keys 'romix', 'dutott', 
            'astot', 'tg'. Each contains per-band values.
        glint_ave : dict
            Glint correction parameters per band (surface reflectance ratios).
        bands : list of str
            List of band names processed.
        """
        # Extract dark spectrum
        pdark = self.compute_pdark(image, settings)

        # Get geometry and atmospheric parameters
        raa = image.get('raa').getInfo()
        vza = image.get('vza').getInfo()
        sza = image.get('sza').getInfo()

        geometry = {
            'raa': raa,
            'vza': vza,
            'sza': sza,
            'pressure': settings['pressure']
        }

        # Get sensor and load LUTs
        sensor = 'S2A_MSI' if 'S2A' in image.get('PRODUCT_ID').getInfo() else 'S2B_MSI'
        
        lutd = self.acolite.aerlut.import_luts(sensor=sensor)
        rsrd = self.acolite.shared.rsr_dict(sensor=sensor)[sensor]
        ttg = self.acolite.ac.gas_transmittance(sza, vza, 
                                                pressure=settings['pressure'], 
                                                uoz=settings['uoz'], 
                                                uwv=settings['uwv'], 
                                                rsr=rsrd['rsr'])
        luti = self.acolite.aerlut.import_rsky_luts(models=[1,2], 
                                                     lutbase='ACOLITE-RSKY-202102-82W', 
                                                     sensor=sensor)

        # Step 1: Estimate AOT for each LUT model
        results = self.estimate_aot_per_lut(pdark, lutd, rsrd, ttg, geometry, 
                                           settings, aot_skip_bands)
        
        # Step 2: Select best model
        sel_lut, sel_aot, sel_par, sel_val = self.select_best_model(results, lutd, 
                                                                     geometry, settings)
        
        print(f'Selected model {sel_lut}: AOT={sel_aot:.3f}, {sel_par}={sel_val:.4e}')
        print(f'  Geometry: SZA={geometry["sza"]:.2f}°, VZA={geometry["vza"]:.2f}°, RAA={geometry["raa"]:.2f}°')
        print(f'  Pressure: {geometry["pressure"]:.2f} hPa')

        # Step 3: Compute atmospheric correction parameters for selected model
        am = {}
        for par in lutd[sel_lut]['ipd']:
            am[par] = {b: lutd[sel_lut]['rgi'][b]((geometry['pressure'], 
                                                   lutd[sel_lut]['ipd'][par], 
                                                   raa, vza, sza, sel_aot))
                        for b in rsrd['rsr_bands']}
        am.update({'tg': ttg['tt_gas']})

        # Step 4: Compute glint correction parameters (AOT floored as in ACOLITE)
        model = int(sel_lut[-1])
        glint_ave = self.compute_glint_ratios(luti, model, geometry, sel_aot,
                                              rsrd['rsr_bands'], settings)

        return am, glint_ave, rsrd['rsr_bands']
    
    def compute_correction_with_fixed_aot(self, image: ee.Image, aot: float, lut_name: str, 
                                         settings: dict) -> Tuple[dict, dict, List[str]]:
        """
        Compute atmospheric correction parameters using fixed AOT and LUT.
        
        Alternative to dark spectrum fitting. Directly computes atmospheric
        correction parameters for a user-specified AOT value and atmospheric
        model. Useful for sensitivity analysis or when AOT is known a priori.
        
        Parameters
        ----------
        image : ee.Image
            Input image with TOA reflectance and geometry metadata.
        aot : float
            Fixed aerosol optical thickness at 550nm.
        lut_name : str
            LUT name (e.g., 'ACOLITE-LUT-202110-MOD2').
        settings : dict
            Processing settings including pressure, ozone, water vapor.
        
        Returns
        -------
        am : dict
            Atmospheric correction parameters with keys 'romix', 'dutott',
            'astot', 'tg'. Each contains per-band values.
        glint_ave : dict
            Glint correction parameters per band.
        bands : list of str
            List of band names processed.
        
        Raises
        ------
        ValueError
            If specified LUT name is not found in available LUTs.
        """
        # Extract geometry from image
        raa = image.get('raa').getInfo()
        vza = image.get('vza').getInfo()
        sza = image.get('sza').getInfo()
        
        geometry = {
            'raa': raa,
            'vza': vza,
            'sza': sza,
            'pressure': settings['pressure']
        }
        
        # Get sensor
        sensor = 'S2A_MSI' if 'S2A' in image.get('PRODUCT_ID').getInfo() else 'S2B_MSI'
        
        # Load specified LUT
        lutd = self.acolite.aerlut.import_luts(sensor=sensor)
        
        # Verify LUT exists
        if lut_name not in lutd:
            available_luts = list(lutd.keys())
            raise ValueError(f"LUT '{lut_name}' not found. Available LUTs: {available_luts}")
        
        # Get RSR data
        rsrd = self.acolite.shared.rsr_dict(sensor=sensor)[sensor]
        pressure = settings['pressure']
        uoz = settings['uoz']
        uwv = settings['uwv']

        # Compute gas transmittance
        ttg = self.acolite.ac.gas_transmittance(sza, vza, 
                                                pressure=pressure, 
                                                uoz=uoz, 
                                                uwv=uwv, 
                                                rsr=rsrd['rsr'])
        
        # Load sky glint LUTs
        luti = self.acolite.aerlut.import_rsky_luts(models=[1,2], 
                                                     lutbase='ACOLITE-RSKY-202102-82W', 
                                                     sensor=sensor)
        
        print(f'Using fixed AOT={aot:.3f} with LUT={lut_name}')
        print(f'  Geometry: SZA={geometry["sza"]:.2f}°, VZA={geometry["vza"]:.2f}°, RAA={geometry["raa"]:.2f}°')
        print(f'  Pressure: {geometry["pressure"]:.2f} hPa')
        
        # Compute atmospheric correction parameters for specified LUT and AOT
        am = {}
        for par in lutd[lut_name]['ipd']:
            am[par] = {b: lutd[lut_name]['rgi'][b]((geometry['pressure'], 
                                                     lutd[lut_name]['ipd'][par], 
                                                     raa, vza, sza, aot))
                        for b in rsrd['rsr_bands']}
        am.update({'tg': ttg['tt_gas']})
        
        # Compute glint correction parameters (AOT floored as in ACOLITE)
        model = int(lut_name[-1])  # Extract model number from LUT name
        glint_ave = self.compute_glint_ratios(luti, model, geometry, aot,
                                              rsrd['rsr_bands'], settings)
        
        return am, glint_ave, rsrd['rsr_bands']
    
    @staticmethod
    def _glint_aot_floor(settings: dict) -> float:
        """
        Return the AOT floor used to evaluate the glint ratios (0.0 = no floor).

        Reads ``glint_aot_floor`` (default 0.1, the value ACOLITE hard-codes in
        ``acolite_l2r.py``: ``gc_aot = max(0.1, ac_aot_550)``). ``0``, ``None`` and the
        strings ``'none'`` / ``'false'`` disable the floor (legacy behaviour of
        gee_acolite <= 1.2.x). Numeric strings are accepted because settings files are
        text.
        """
        value = settings.get('glint_aot_floor', 0.1) if settings else 0.1
        if value is None or value is False:
            return 0.0
        if isinstance(value, str):
            if value.strip().lower() in ('', 'none', 'false', 'off'):
                return 0.0
            value = float(value)
        return max(0.0, float(value))

    def compute_glint_ratios(self, luti: dict, model: int, geometry: dict, aot: float,
                             rsr_bands: List[str], settings: dict) -> dict:
        """
        Compute the per-band sky-glint (interface reflectance) ratios used by
        :meth:`deglint_alternative`.

        For each band the ratio is ``rsky(band) / mean(rsky(B11), rsky(B12))`` evaluated
        with the sky-reflectance LUT at wind speed 20 m/s. As in ACOLITE
        (``acolite_l2r.py`` ~1618) the LUT is evaluated at ``gc_aot = max(floor, aot)``
        with ``floor = glint_aot_floor`` (default 0.1). Only the glint ratios use the
        floored AOT; the atmospheric correction keeps the real selected AOT.

        Why the floor matters: the rsky LUT is exactly 0 in B11/B12 for AOT <= 0.05, so
        the legacy ratio (evaluated at the raw AOT) was infinite and
        ``deglint_alternative`` skipped every band, i.e. the residual glint correction was
        silently disabled. For AOT in (0.05, 0.1) the legacy ratio was exaggerated
        (e.g. B2 ratio 4.95 at AOT 0.06 and 1.65 at 0.08 in the real LUT), which removed
        too much glint.

        Parameters
        ----------
        luti : dict
            Sky-reflectance LUTs keyed by model number (``import_rsky_luts``).
        model : int
            Aerosol model number (1 or 2).
        geometry : dict
            Dict with 'raa', 'vza', 'sza'.
        aot : float
            Selected (or fixed) AOT at 550 nm.
        rsr_bands : list of str
            Band identifiers to evaluate (must include '11' and '12').
        settings : dict
            Processing settings. Key read: ``glint_aot_floor``.

        Returns
        -------
        dict
            Ratio per band. If the SWIR reference mean is not finite or not positive
            (degenerate LUT) a ``UserWarning`` is emitted and every ratio is NaN, so
            that ``deglint_alternative`` skips glint correction instead of receiving inf.
        """
        glint_wind = 20
        glint_bands = ['11', '12']
        gc_aot = max(self._glint_aot_floor(settings), float(aot))

        glint_dict = {b: luti[model]['rgi'][b]((geometry['raa'], geometry['vza'], geometry['sza'],
                                                glint_wind, gc_aot))
                      for b in rsr_bands}
        reference = (glint_dict[glint_bands[0]] + glint_dict[glint_bands[1]]) / 2

        if not np.isfinite(reference) or reference <= 0:
            warnings.warn(
                f'Residual glint correction skipped: the SWIR reference sky reflectance is '
                f'{float(reference):.4g} at AOT {gc_aot:.3f} (model {model}). Use a larger '
                f'glint_aot_floor (ACOLITE uses 0.1).', UserWarning, stacklevel=2)
            return {b: np.nan for b in glint_dict}

        return {b: glint_dict[b] / reference for b in glint_dict}

    def compute_pdark(self, image : ee.Image, settings : dict):
        """
        Compute dark spectrum values from an image.
        
        Extracts dark pixel reflectance values for each band using one of
        three methods: darkest pixels (minimum over all valid pixels),
        percentile-based, or linear intercept method.
        
        Parameters
        ----------
        image : ee.Image
            Input image with TOA reflectance.
        settings : dict
            Processing settings including 'dsf_spectrum_option', 
            'dsf_percentile', 'dsf_intercept_pixels'.
        
        Returns
        -------
        pdark_by_band : dict
            Dictionary with dark spectrum values per band (e.g., {'B1': 0.05, ...}).
        """
        obands_rhot = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']

        image_to_reduce = image.updateMask(image.gt(0))

        pdark_by_band = {}
        indexes = np.arange(settings['dsf_intercept_pixels'])

        for band in obands_rhot:
            if settings.get('dsf_spectrum_option', 'darkest') == 'darkest':
                # True minimum over every valid pixel (as ACOLITE). bestEffort is not
                # used: it subsamples large tiles and raises the minimum.
                band_data = image_to_reduce.select(band).reduceRegion(reducer = ee.Reducer.min(),
                                                        scale = 10, maxPixels = 1e10, tileScale = 4)

                if band_data:
                    value = band_data.getInfo()[band]
                    # No valid pixel for this band: NaN, so it drops out of the AOT ranking
                    pdark_by_band[band] = np.nan if value is None else value
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
        """
        Compute surface reflectance from TOA reflectance.
        
        Applies atmospheric correction using computed atmospheric parameters
        to derive surface reflectance. Also adds TOA reflectance bands to
        the output image.
        
        Parameters
        ----------
        image : ee.Image
            Input image with TOA reflectance bands.
        am : dict
            Atmospheric correction parameters with keys 'romix' (path reflectance),
            'dutott' (total upward transmittance), 'astot' (spherical albedo),
            'tg' (gas transmittance).
        
        Returns
        -------
        l2r_rrs : ee.Image
            Image with both TOA reflectance (rhot_*) and surface reflectance
            (rhos_*) bands.
        """
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
        """
        Retrieve ancillary atmospheric data from NASA Earthdata.
        
        Fetches ozone, water vapor, wind speed, and surface pressure data
        from NASA GMAO or NCEP reanalysis products for the image location
        and acquisition time.
        
        Parameters
        ----------
        image : ee.Image
            Input image with geometry and timestamp.
        settings : dict
            Processing settings including Earthdata credentials and default values.
        
        Returns
        -------
        settings : dict
            Updated settings with ancillary data values.
        """
        settings = self.prepare_earthdata_credentials(settings)
        iso_date, lon, lat = self.prepare_query(image)

        anc = self.acolite.ac.ancillary.get(iso_date, lon, lat)

        for data, default in [('uoz', 'uoz_default'), ('uwv', 'uwv_default'), 
                            ('wind', 'wind_default'), ('pressure', 'pressure_default')]:
            settings[data] = anc.get(data, settings.get(default)) 
        
        return settings

    def prepare_query(self, image: ee.Image):
        """
        Extract location and timestamp from image for ancillary data query.
        
        Parameters
        ----------
        image : ee.Image
            Input image with geometry and timestamp metadata.
        
        Returns
        -------
        iso_date : str
            ISO formatted date string.
        lon : float
            Longitude of image centroid.
        lat : float
            Latitude of image centroid.
        """
        coords = image.geometry().centroid().coordinates().getInfo()
        iso_date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd HH:mm:ss').getInfo()

        lon, lat = coords
        return iso_date,lon,lat

    def prepare_earthdata_credentials(self, settings: dict) -> dict:
        """
        Set NASA Earthdata credentials as environment variables.
        
        Parameters
        ----------
        settings : dict
            Settings dictionary potentially containing 'EARTHDATA_u' and 'EARTHDATA_p'.
        
        Returns
        -------
        settings : dict
            Input settings dictionary (unchanged).
        """
        for k in ['EARTHDATA_u', 'EARTHDATA_p']:
            kv = settings[k] if k in settings else self.acolite.ac.config[k]
            if len(kv) == 0: continue
            os.environ[k] = kv
        
        return settings


    def deglint_alternative(self, image : ee.Image, bands : List[str], 
                            glint_ave : dict, glint_min : float = 0, glint_max : float = 0.08) -> ee.Image:
        """
        Remove residual sun glint from surface reflectance image.
        
        Alternative glint correction method based on ACOLITE's implementation.
        Uses SWIR bands (B11, B12) as reference to estimate and remove glint
        contamination. The glint signal is spectrally scaled based on modeled
        surface reflectance ratios.
        
        Workflow:
        1. Computes observed glint as average of SWIR reference bands (B11, B12)
        2. Calculates average modeled surface reflectance for reference bands
        3. For each band, scales observed glint by ratio of modeled reflectances
        4. Subtracts scaled glint from surface reflectance
        
        Parameters
        ----------
        image : ee.Image
            Image with surface reflectance (rhos_*) bands.
        bands : list of str
            List of band numbers to correct (as strings, e.g., ['1', '2', ...]).
        glint_ave : dict
            Modeled surface reflectance ratios per band.
        glint_min : float, optional
            Minimum threshold for glint mask (default: 0).
        glint_max : float, optional
            Maximum threshold for glint mask (default: 0.08).
        
        Returns
        -------
        deglinted : ee.Image
            Image with glint-corrected surface reflectance bands.
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