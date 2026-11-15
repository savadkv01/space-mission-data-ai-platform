-- Serving data product: Flood Extent (UC-16). Mirrors serve_flood_daily.
-- flood_flag is decided only from NDWI statistics with the permanent-water mask
-- (water_mask: JRC GSW seasonality >= 10 months + ESA WorldCover permanent water):
-- new open water on at least 2% of the valid non-permanent pixels. Legacy unmasked
-- rows (cannot separate sea from flood water) and days with < 10% valid pixels
-- are 'not_evaluated' (flag null), never negative.
with flood as (
    select * from {{ source('gold', 'kpi_flood_aoi_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
),
corr as (
    select aoi_key
    from {{ source('gold', 'kpi_aoi_validation') }}
    where event_type = 'flood' and corroborated
)
select
    f.aoi_key,
    a.aoi_name,
    a.region,
    coalesce(a.rollup_eligible, true) as rollup_eligible,
    f.date_key,
    f.ndwi_mean,
    f.ndwi_max,
    f.valid_pixel_fraction,
    f.water_fraction,
    f.permanent_water_fraction,
    f.water_mask,
    f.flood_flag,
    case
        when f.flood_flag then 'positive'
        when not f.flood_flag then 'negative'
        else 'not_evaluated'
    end                               as flood_status,
    a.area_km2,
    (c.aoi_key is not null) as ems_corroborated
from flood f
left join aoi  a on f.aoi_key = a.aoi_key
left join corr c on f.aoi_key = c.aoi_key
