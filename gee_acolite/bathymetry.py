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
    num_points: int = 20,
    seed: int = 42,
    scale: int = 10
) -> dict:
    """
    Calibrate satellite-derived bathymetry using random sample points.

    This function selects random points from areas with valid in-situ bathymetry
    data up to a specified maximum depth, and performs linear regression to
    establish a calibration relationship.

    Parameters
    ----------
    psdb_image : ee.Image
        Pseudo-SDB image (e.g., pSDB_green band) to calibrate
    insitu_bathymetry : ee.Image
        In-situ bathymetry reference image with depth values
    region : ee.Geometry
        Region of interest for sampling
    max_depth : float, optional
        Maximum depth in meters for calibration points (default: 10)
    num_points : int, optional
        Maximum number of random points to sample (default: 20)
    seed : int, optional
        Random seed for reproducibility (default: 42)
    scale : int, optional
        Scale in meters for sampling (default: 10)

    Returns
    -------
    dict
        Dictionary containing:
        - 'slope': Regression slope coefficient
        - 'intercept': Regression intercept coefficient
        - 'correlation': Pearson correlation coefficient
        - 'num_points': Number of valid points used
        - 'sample_fc': ee.FeatureCollection of sampled points

    Examples
    --------
    >>> result = calibrate_sdb(
    ...     psdb_image=image.select('pSDB_green'),
    ...     insitu_bathymetry=bathymetry_image,
    ...     region=roi,
    ...     max_depth=10,
    ...     num_points=20
    ... )
    >>> print(f"SDB = {result['slope']:.4f} * pSDB + {result['intercept']:.4f}")
    """
    # Combine images for sampling
    combined = psdb_image.addBands(insitu_bathymetry.rename('depth'))
    
    # Create mask for valid depth values (0 < depth <= max_depth)
    depth_mask = insitu_bathymetry.gt(0).And(insitu_bathymetry.lte(max_depth))
    
    # Create mask for valid pSDB values (not null/masked)
    psdb_mask = psdb_image.mask().reduce(ee.Reducer.min())
    
    # Apply both masks: only sample where both depth AND pSDB are valid
    combined_filtered = combined.updateMask(depth_mask).updateMask(psdb_mask)
    
    # Sample random points
    sample_fc = combined_filtered.sample(
        region=region,
        scale=scale,
        numPixels=num_points,
        seed=seed,
        geometries=True
    )
    
    # Get band name from psdb_image
    psdb_band_name = psdb_image.bandNames().get(0).getInfo()
    
    # Perform linear regression
    regression = sample_fc.reduceColumns(
        reducer=ee.Reducer.linearFit(),
        selectors=[psdb_band_name, 'depth']
    )
    
    # Calculate Pearson correlation
    correlation = sample_fc.reduceColumns(
        reducer=ee.Reducer.pearsonsCorrelation(),
        selectors=[psdb_band_name, 'depth']
    )
    
    # Get results
    regression_info = regression.getInfo()
    correlation_info = correlation.getInfo()
    num_sampled = sample_fc.size().getInfo()
    
    return {
        'slope': regression_info['scale'],
        'intercept': regression_info['offset'],
        'correlation': correlation_info['correlation'],
        'num_points': num_sampled,
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