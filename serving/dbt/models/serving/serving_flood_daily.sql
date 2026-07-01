-- Serving data product: Flood Extent (UC-16). Mirrors serve_flood_daily.
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
    f.date_key,
    f.ndwi_mean,
    f.ndwi_max,
    f.valid_pixel_fraction,
    f.flood_flag,
    a.area_km2,
    (c.aoi_key is not null) as ems_corroborated
from flood f
left join aoi  a on f.aoi_key = a.aoi_key
left join corr c on f.aoi_key = c.aoi_key
