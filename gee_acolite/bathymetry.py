"""
Bathymetry utilities for satellite-derived bathymetry (SDB) processing.
"""
import ee


def optical_deep_water_model(
    model: ee.Image,
    blue: ee.Image,
    green: ee.Image,
    vnir: ee.Image
) -> ee.Image:
    """
    Filter depth estimations based on optical properties of water.

    This function applies optical water property-based filters to depth estimation
    models to improve accuracy. It filters out pixels based on reflectance thresholds
    for clear waters and an upper depth limit equation for turbid waters as described
    in peer-reviewed literature.

    Parameters
    ----------
    model : ee.Image
        The initial depth estimation model output to be filtered
    blue : ee.Image
        Blue band reflectance values, used for clear water filtering
    green : ee.Image
        Green band reflectance values, used for clear water filtering
    vnir : ee.Image
        Near-infrared band reflectance values, used for turbid water depth limit calculation

    Returns
    -------
    ee.Image
        Filtered depth model with invalid estimations masked out

    Notes
    -----
    The function applies two filtering steps:
    1. Clear water filtering: removes pixels with reflectance <= 0.003 in blue or green bands
    2. Turbid water filtering: applies depth limitation based on NIR reflectance using the equation:
       Ymax = -0.251 * ln(NIR) + 0.8

    References
    ----------
    Caballero, I., & Stumpf, R. P. (2019). Retrieval of nearshore bathymetry from Sentinel-2A and 2B
    satellites in South Florida coastal waters. Estuarine, Coastal and Shelf Science, 226, 106277.
    https://doi.org/10.1016/j.ecss.2019.106277
    """
    # Clear waters mask: remove pixels with reflectance <= 0.003 in blue or green bands
    clear_water_mask = blue.gt(0.003).And(green.gt(0.003))
    
    # Turbid waters: calculate depth limit based on NIR reflectance
    # Ymax = -0.251 * ln(NIR) + 0.8
    Ymax = vnir.log().multiply(-0.251).add(0.8)
    Ymax = Ymax.updateMask(Ymax.gt(0))
    
    # Calculate y = ln(model) and mask negative values
    y = model.log()
    y = y.updateMask(y.gt(0))
    
    # Turbid water mask: y <= Ymax
    turbid_water_mask = y.lte(Ymax)
    
    # Apply both masks
    filtered_model = model.updateMask(clear_water_mask).updateMask(turbid_water_mask)
    
    return filtered_model


def calibrate_sdb(
    psdb_image: ee.Image,
    insitu_bathymetry: ee.Image,
    region: ee.Geometry,
    max_depth: float = 10,
    num_sample_points: int = 500,
    seed: int = 42,
    scale: int = 10
) -> dict:
    """
    Calibrate satellite-derived bathymetry using linear regression.

    Performs pixel-wise linear regression between a pseudo-SDB image and
    in-situ bathymetry using all valid overlapping pixels up to `max_depth`.
    A random subsample is also returned for scatter plot visualization.

    Parameters
    ----------
    psdb_image : ee.Image
        Pseudo-SDB image (e.g., pSDB_green band) to calibrate
    insitu_bathymetry : ee.Image
        In-situ bathymetry image with depth values in metres (positive = deeper)
    region : ee.Geometry
        Region of interest for the regression
    max_depth : float, optional
        Maximum depth in metres for calibration pixels (default: 10)
    num_sample_points : int, optional
        Number of random points to draw for the visualisation sample
        (default: 500). Does **not** affect regression coefficients.
    seed : int, optional
        Random seed for the visualisation sample (default: 42)
    scale : int, optional
        Pixel scale in metres (default: 10)

    Returns
    -------
    dict
        Dictionary containing:

        - ``'slope'``: Regression slope coefficient
        - ``'intercept'``: Regression intercept coefficient
        - ``'correlation'``: Pearson correlation coefficient
        - ``'num_pixels'``: Number of valid pixels used in the regression
        - ``'sample_fc'``: ``ee.FeatureCollection`` of random points for plotting

    Notes
    -----
    Regression is computed with ``ee.Reducer.linearFit()`` over all valid pixels
    (``reduceRegion``), which is more robust than point sampling when in-situ and
    satellite data have sparse spatial overlap.

    Examples
    --------
    >>> result = calibrate_sdb(
    ...     psdb_image=image.select('pSDB_green'),
    ...     insitu_bathymetry=bathy_image,
    ...     region=roi,
    ...     max_depth=10,
    ... )
    >>> print(f"SDB = {result['slope']:.4f} * pSDB + {result['intercept']:.4f}")
    """
    psdb_band_name = psdb_image.bandNames().get(0).getInfo()

    # Mask: valid depth range AND valid pSDB pixel
    depth_mask = insitu_bathymetry.gt(0).And(insitu_bathymetry.lte(max_depth))
    psdb_mask = psdb_image.mask().reduce(ee.Reducer.min())
    valid_mask = depth_mask.And(psdb_mask)

    combined = psdb_image.addBands(insitu_bathymetry.rename('depth')).updateMask(valid_mask)

    # --- Regression over all valid pixels ---
    regression = combined.reduceRegion(
        reducer=ee.Reducer.linearFit().setOutputs(['scale', 'offset']),
        geometry=region,
        scale=scale,
        maxPixels=1e9
    )

    # --- Pearson correlation ---
    correlation = combined.reduceRegion(
        reducer=ee.Reducer.pearsonsCorrelation(),
        geometry=region,
        scale=scale,
        maxPixels=1e9
    )

    # --- Pixel count ---
    pixel_count = combined.select(psdb_band_name).reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=region,
        scale=scale,
        maxPixels=1e9
    )

    # --- Random subsample for visualisation ---
    sample_fc = combined.sample(
        region=region,
        scale=scale,
        numPixels=num_sample_points,
        seed=seed,
        geometries=True
    )

    regression_info = regression.getInfo()
    correlation_info = correlation.getInfo()
    count_info = pixel_count.getInfo()

    return {
        'slope': regression_info.get('scale'),
        'intercept': regression_info.get('offset'),
        'correlation': correlation_info.get('correlation'),
        'num_pixels': count_info.get(psdb_band_name),
        'sample_fc': sample_fc
    }


def apply_calibration(
    psdb_image: ee.Image,
    slope: float,
    intercept: float,
    output_name: str = 'SDB'
) -> ee.Image:
    """
    Apply calibration coefficients to a pseudo-SDB image.

    Parameters
    ----------
    psdb_image : ee.Image
        Pseudo-SDB image to calibrate
    slope : float
        Regression slope coefficient
    intercept : float
        Regression intercept coefficient
    output_name : str, optional
        Name for the output band (default: 'SDB')

    Returns
    -------
    ee.Image
        Calibrated SDB image

    Examples
    --------
    >>> sdb = apply_calibration(
    ...     psdb_image=image.select('pSDB_green'),
    ...     slope=result['slope'],
    ...     intercept=result['intercept'],
    ...     output_name='SDB_green'
    ... )
    """
    return psdb_image.multiply(slope).add(intercept).rename(output_name)


def multi_image(images: ee.ImageCollection, band: str = 'pSDB_green') -> ee.Image:
    """
    Create a quality mosaic from multiple images based on a bathymetry band.
    
    Selects the best pixel values from a collection of images based on the
    quality of a specified bathymetry band (e.g., pseudo-Satellite Derived Bathymetry).
    
    Parameters
    ----------
    images : ee.ImageCollection
        Collection of images containing bathymetry bands.
    band : str, optional
        Band name to use for quality assessment (default: 'pSDB_green').
        Pixels with higher values in this band are prioritized.
    
    Returns
    -------
    ee.Image
        Quality mosaic image with the best pixels from the collection.
    
    Examples
    --------
    >>> images = ee.ImageCollection([image1, image2, image3])
    >>> mosaic = multi_image(images, band='pSDB_red')
    """
    return images.qualityMosaic(band)