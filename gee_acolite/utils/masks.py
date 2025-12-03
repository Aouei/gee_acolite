import ee


def mask_negative_reflectance(image : ee.Image, band : str) -> ee.Image:
    return image.updateMask(image.select(band).gte(0)).rename(band)

def toa_mask(image : ee.Image, band : str = 'rhot_B11', threshold : float = 0.03):
    return image.select(band).lt(threshold)

def cirrus_mask(image : ee.Image, band : str = 'rhot_B10', threshold : float = 0.005):
    return image.select(band).lt(threshold)

def non_water(image : ee.Image, band : str = 'rhot_B11', threshold : float = 0.05) -> ee.Image:
    return image.select(band).lt(threshold)


def add_cloud_bands(img : ee.Image, cloud_prob_threshold : float = 50) -> ee.Image:
    """
    Añade banda de máscara de nubes a la imagen
    
    Args:
        img: Imagen con banda 'probability' de Cloud Probability
        cloud_prob_threshold: Umbral de probabilidad de nube (0-100)
        
    Returns:
        Imagen con banda 'clouds' añadida
    """
    # Obtener probabilidad de nubes (ya está como banda)
    cld_prb = ee.Image(img.get('cloud_prob')).select('probability')
    
    # Máscara de nubes basada en umbral de probabilidad
    is_cloud = cld_prb.gt(cloud_prob_threshold).rename('clouds')
    
    return img.addBands(is_cloud)


def add_shadow_bands(img : ee.Image, nir_dark_threshold : float = 0.15, 
                     cloud_proj_distance : float = 1) -> ee.Image:
    """
    Añade bandas de máscara de sombras a la imagen L1C
    
    Args:
        img: Imagen con banda 'clouds' ya añadida
        nir_dark_threshold: Umbral para píxeles oscuros en NIR (0-1)
        cloud_proj_distance: Distancia de proyección de sombras en km
        
    Returns:
        Imagen con bandas 'dark_pixels', 'cloud_transform' y 'shadows' añadidas
    """
    # Píxeles oscuros en NIR (posibles sombras) - para L1C usar B8 directamente
    dark_pixels = img.select('rhot_B8').lt(nir_dark_threshold * 10000).rename('dark_pixels')
    
    # Dirección de proyección de sombras
    shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')))
    
    # Proyectar sombras desde nubes
    cld_proj = img.select('clouds').directionalDistanceTransform(shadow_azimuth, cloud_proj_distance * 10) \
        .reproject(**{'crs': img.select(0).projection(), 'scale': 100}) \
        .select('distance') \
        .mask() \
        .rename('cloud_transform')
    
    # Identificar sombras como intersección de píxeles oscuros y proyección de nubes
    shadows = cld_proj.multiply(dark_pixels).rename('shadows')
    
    return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))


def add_cld_shdw_mask(img : ee.Image, cloud_prob_threshold : float = 50, 
                      nir_dark_threshold : float = 0.15, cloud_proj_distance : float = 1, 
                      buffer : int = 50) -> ee.Image:
    """
    Añade máscara combinada de nubes y sombras con buffer
    
    Args:
        img: Imagen con banda 'probability' de Cloud Probability
        cloud_prob_threshold: Umbral de probabilidad de nube (0-100)
        nir_dark_threshold: Umbral para píxeles oscuros en NIR (0-1)
        cloud_proj_distance: Distancia de proyección de sombras en km
        buffer: Buffer alrededor de nubes en metros
        
    Returns:
        Imagen con banda 'cloudmask' añadida
    """
    # Añadir bandas de nubes
    img_cloud = add_cloud_bands(img, cloud_prob_threshold)
    
    # Añadir bandas de sombras
    img_cloud_shadow = add_shadow_bands(img_cloud, nir_dark_threshold, cloud_proj_distance)
    
    # Combinar máscaras
    is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)
    
    # Aplicar buffer
    is_cld_shdw = is_cld_shdw.focal_min(2).focal_max(buffer * 2 / 20) \
        .reproject(**{'crs': img.select([0]).projection(), 'scale': 20}) \
        .rename('cloudmask')
    
    return img_cloud_shadow.addBands(is_cld_shdw)


def cld_shdw_mask(img : ee.Image) -> ee.Image:
    """
    Aplica la máscara de nubes y sombras a la imagen
    
    Args:
        img: Imagen con banda 'cloudmask' ya añadida
        
    Returns:
        Imagen enmascarada con solo las bandas B* (bandas Sentinel-2)
    """
    # Obtener máscara
    return img.select('cloudmask').Not()