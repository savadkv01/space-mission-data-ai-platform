-- Serving data product: Climate Indicator. Mirrors
-- serving.marts.climate.climate_products.serve_climate_indicator_daily. Wide,
-- business-named, and pre-joined to dim_aoi so BI/API read with no runtime joins.
with clim as (
    select * from {{ source('gold', 'fact_climate_indicator_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
)
select
    c.aoi_key,
    a.aoi_name,
    c.date_key,
    c.lst_c,
    c.lst_anomaly_c,
    c.sst_c,
    c.sst_anomaly_c,
    c.ndwi_mean,
    c.tree_cover_loss_ha,
    c.desertification_proxy,
    c.lst_anomaly_band,
    case c.lst_anomaly_band
        when -1 then 'Cooler'
        when 0  then 'Normal'
        when 1  then 'Warm'
        when 2  then 'Hot'
        when 3  then 'Extreme'
        else 'unknown'
    end                                                   as lst_anomaly_label,
    c.warming_flag,
    c.desertification_flag,
    a.area_km2
from clim c
left join aoi a on c.aoi_key = a.aoi_key
