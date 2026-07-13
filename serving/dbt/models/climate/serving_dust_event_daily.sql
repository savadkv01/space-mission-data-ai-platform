-- Serving data product: Dust Event. Mirrors
-- serving.marts.climate.climate_products.serve_dust_event_daily. Wide,
-- business-named, and pre-joined to dim_aoi so BI/API read with no runtime joins.
with dust as (
    select * from {{ source('gold', 'fact_dust_event_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
)
select
    d.aoi_key,
    a.aoi_name,
    d.date_key,
    d.aod_mean,
    d.aod_max,
    d.uv_aerosol_index_mean,
    d.wind_speed_mean,
    d.wind_dir_dominant,
    d.corridor_aod_max,
    d.valid_fraction,
    d.dust_severity_band,
    case d.dust_severity_band
        when 0 then 'Clear'
        when 1 then 'Hazy'
        when 2 then 'Dusty'
        when 3 then 'Heavy dust'
        when 4 then 'Severe'
        else 'unknown'
    end                                                   as dust_severity_label,
    d.dust_flag,
    d.transport_flag,
    a.area_km2
from dust d
left join aoi a on d.aoi_key = a.aoi_key
