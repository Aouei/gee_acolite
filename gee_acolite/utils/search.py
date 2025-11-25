import ee

from typing import Optional


def search(roi : ee.Geometry, start : str, end : str, 
           collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    if tile is None:
        sentinel2_l1 = ee.ImageCollection(f'COPERNICUS/{collection}').filterBounds(roi).filterDate(start, end)
    else:
        sentinel2_l1 = ee.ImageCollection(f'COPERNICUS/{collection}').filterBounds(roi).filterDate(start, end).filter(ee.Filter.stringContains('PRODUCT_ID', tile))

    return sentinel2_l1

def search_list(roi : ee.Geometry, starts : list[str], ends : list[str], 
                collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    
    return ee.ImageCollection.fromImages([search(roi, start, end, collection, tile).first() for start, end in zip(starts, ends)])


def search_with_cloud_proba(roi : ee.Geometry, start : str, end : str, 
                            collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    """
    Busca imágenes Sentinel-2 y une con Cloud Probability
    
    Args:
        roi: Región de interés
        start: Fecha de inicio (formato 'YYYY-MM-DD')
        end: Fecha de fin (formato 'YYYY-MM-DD')
        collection: Nombre de la colección de Sentinel-2 (default: 'S2_HARMONIZED')
        tile: Identificador del tile (opcional)
        
    Returns:
        Colección de imágenes con Cloud Probability unida
    """
    s2_collection = search(roi, start, end, collection, tile)
    return join_s2_with_cloud_prob(s2_collection)


def search_list_with_cloud_proba(roi : ee.Geometry, starts : list[str], ends : list[str], 
                                 collection : str = 'S2_HARMONIZED', tile : Optional[str] = None) -> ee.ImageCollection:
    """
    Busca una lista de imágenes Sentinel-2 y une con Cloud Probability
    
    Args:
        roi: Región de interés
        starts: Lista de fechas de inicio (formato 'YYYY-MM-DD')
        ends: Lista de fechas de fin (formato 'YYYY-MM-DD')
        collection: Nombre de la colección de Sentinel-2 (default: 'S2_HARMONIZED')
        tile: Identificador del tile (opcional)
        
    Returns:
        Colección de imágenes con Cloud Probability unida
    """
    s2_collection = search_list(roi, starts, ends, collection, tile)
    return join_s2_with_cloud_prob(s2_collection)


def join_s2_with_cloud_prob(s2_collection : ee.ImageCollection) -> ee.ImageCollection:
    """
    Une la colección Sentinel-2 con Cloud Probability
    
    Args:
        s2_collection: Colección de imágenes Sentinel-2 L1C
        roi: Región de interés
        
    Returns:
        Colección de imágenes con Cloud Probability unida como propiedad 'cloud_prob'
    """
    
    def add_cloud_prob(img):
        img_index = img.get('system:index')
        cloud = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY') \
            .filter(ee.Filter.equals('system:index', img_index)) \
            .first()
        
        return img.set('cloud_prob', cloud)
    
    return s2_collection.map(add_cloud_prob)