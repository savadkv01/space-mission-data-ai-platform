-- Semantic: climate-indicator dimension (Phase 11b). Conformed dimension
-- carrying business-friendly names, units and source family for the climate and
-- vegetation products, classification bands and ingest requirements. Static reference data single-sourced with
-- serving.marts.semantic.CLIMATE_INDICATORS (there is no upstream Gold table).
select * from (
    values
        ('LST', 'Land Surface Temperature', '°C', 'MODIS/Landsat', 'daily', CAST(NULL AS JSON), CAST('[]' AS JSON), false),
        ('LST_ANOM', 'LST Anomaly (same-DOY)', '°C', 'derived', 'daily', CAST(NULL AS JSON),
         CAST('[{"band":-1,"label":"Cooler","value_low":null,"value_high":-1.0},{"band":0,"label":"Normal","value_low":-1.0,"value_high":1.0},{"band":1,"label":"Warm","value_low":1.0,"value_high":3.0},{"band":2,"label":"Hot","value_low":3.0,"value_high":5.0},{"band":3,"label":"Extreme","value_low":5.0,"value_high":null}]' AS JSON), false),
        ('SST', 'Sea Surface Temperature', '°C', 'OISST', 'daily', CAST(NULL AS JSON), CAST('[]' AS JSON), false),
        ('SST_ANOM', 'SST Anomaly (same-DOY)', '°C', 'derived', 'daily', CAST(NULL AS JSON), CAST('[]' AS JSON), false),
        ('NDVI', 'Vegetation Index (NDVI)', 'index', 'Sentinel-2', '16-day', CAST('[-1.0,1.0]' AS JSON),
         CAST('[{"band":0,"label":"Bare / water","value_low":-1.0,"value_high":0.1},{"band":1,"label":"Sparse","value_low":0.1,"value_high":0.3},{"band":2,"label":"Moderate","value_low":0.3,"value_high":0.5},{"band":3,"label":"Healthy","value_low":0.5,"value_high":0.7},{"band":4,"label":"Dense","value_low":0.7,"value_high":1.0}]' AS JSON), false),
        ('EVI', 'Enhanced Vegetation Index', 'index', 'Sentinel-2', '16-day', CAST('[-1.0,1.0]' AS JSON), CAST('[]' AS JSON), false),
        ('NDWI', 'Water Index (NDWI)', 'index', 'Sentinel-2', '16-day', CAST('[-1.0,1.0]' AS JSON), CAST('[]' AS JSON), false),
        ('TREE_LOSS', 'Tree-Cover Loss', 'ha', 'GFW', 'annual', CAST(NULL AS JSON), CAST('[]' AS JSON), false),
        ('DESERT_PROXY', 'Desertification Proxy', 'index', 'derived', 'daily', CAST('[0.0,1.0]' AS JSON), CAST('[]' AS JSON), false)
) as t(indicator_code, indicator_name, unit, source_family, native_cadence, normal_range, anomaly_bands, requires_new_ingest)
