-- Semantic: AOI dimension (Task 3). Business-friendly conformed dimension over
-- the curated AOI footprints, joined into every AOI-grained data product so a
-- serving row carries a human-readable AOI name, event context, and analysis
-- region (UAE-GULF / INDIA / US-LEGACY). Regions are never combined in rollups.
-- rollup_eligible AOIs form a non-overlapping reporting partition per region
-- (ADR-12); event overlays (rollup_eligible = false) are never summed.
select
    aoi_key,
    aoi_name,
    event_type,
    region,
    sub_region,
    aoi_role,
    rollup_eligible,
    is_ems_activation,
    cropland,
    area_km2,
    geo_key
from {{ source('gold', 'ref_aoi') }}