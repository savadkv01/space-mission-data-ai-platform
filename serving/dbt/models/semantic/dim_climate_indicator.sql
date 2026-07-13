-- Semantic: climate-indicator dimension (Phase 11b). Conformed dimension
-- carrying business-friendly names, units and source family for the climate and
-- vegetation products. Static reference data single-sourced with
-- serving.marts.semantic.CLIMATE_INDICATORS (there is no upstream Gold table).
select * from (
    values
        ('LST',          'Land Surface Temperature', '°C',       'MODIS/Landsat', 'daily'),
        ('LST_ANOM',     'LST Anomaly (same-DOY)',   '°C',       'derived',       'daily'),
        ('SST',          'Sea Surface Temperature',  '°C',       'OISST',         'daily'),
        ('SST_ANOM',     'SST Anomaly (same-DOY)',   '°C',       'derived',       'daily'),
        ('NDVI',         'Vegetation Index (NDVI)',  'index',    'Sentinel-2',    '16-day'),
        ('EVI',          'Enhanced Vegetation Index','index',    'Sentinel-2',    '16-day'),
        ('NDWI',         'Water Index (NDWI)',       'index',    'Sentinel-2',    '16-day'),
        ('TREE_LOSS',    'Tree-Cover Loss',          'ha',       'GFW',           'annual'),
        ('DESERT_PROXY', 'Desertification Proxy',    'index',    'derived',       'daily')
) as t(indicator_code, indicator_name, unit, source_family, native_cadence)
