-- Semantic: AOI dimension (Task 3). Business-friendly conformed dimension over
-- the curated AOI footprints, joined into every AOI-grained data product so a
-- serving row carries a human-readable AOI name, event context, and analysis
-- region (UAE-GULF / INDIA / US-LEGACY). Regions are never combined in rollups.
select
    aoi_key,
    aoi_name,
    event_type,
    region,
    area_km2,
    geo_key
from {{ source('gold', 'ref_aoi') }}