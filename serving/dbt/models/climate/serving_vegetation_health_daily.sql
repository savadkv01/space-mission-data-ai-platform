-- Serving data product: Vegetation Health. Mirrors
-- serving.marts.climate.climate_products.serve_vegetation_health_daily. Wide,
-- business-named, and pre-joined to dim_aoi so BI/API read with no runtime joins.
with veg as (
    select * from {{ source('gold', 'fact_vegetation_health_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
)
select
    v.aoi_key,
    a.aoi_name,
    v.date_key,
    v.ndvi_mean,
    v.ndvi_max,
    v.evi_mean,
    v.ndvi_trend_30d,
    case
        when v.ndvi_trend_30d is null then 'flat'
        when v.ndvi_trend_30d > 0     then 'improving'
        when v.ndvi_trend_30d < 0     then 'declining'
        else 'flat'
    end                                                   as ndvi_trend_dir,
    v.valid_pixel_fraction,
    v.ndvi_health_band,
    case v.ndvi_health_band
        when 0 then 'Bare / water'
        when 1 then 'Sparse'
        when 2 then 'Moderate'
        when 3 then 'Healthy'
        when 4 then 'Dense'
        else 'unknown'
    end                                                   as ndvi_health_label,
    v.crop_stress_flag,
    a.area_km2
from veg v
left join aoi a on v.aoi_key = a.aoi_key
