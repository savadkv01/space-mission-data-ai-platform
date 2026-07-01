-- Semantic: AOI dimension (Task 3). Business-friendly conformed dimension over
-- the Copernicus-EMS footprints, joined into wildfire/flood data products so a
-- single serving row carries a human-readable AOI name and event context.
select
    aoi_key,
    aoi_name,
    event_type,
    area_km2,
    geo_key
from {{ source('gold', 'ref_aoi') }}
