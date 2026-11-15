-- Serving data product: Climate Indicator. Mirrors
-- serving.marts.climate.climate_products.serve_climate_indicator_daily. Wide,
-- business-named, and pre-joined to dim_aoi so BI/API read with no runtime joins.
-- warming_flag (OR over LST/SST anomalies) is false only when both anomalies are
-- observed; desertification_flag needs the proxy. Otherwise null + status.
with clim as (
    select
        *,
        {{ evidence_status(
            'warming_flag',
            'lst_anomaly_c is not null and sst_anomaly_c is not null',
            'lst_anomaly_c is not null or sst_anomaly_c is not null'
        ) }} as warming_status,
        {{ evidence_status(
            'desertification_flag',
            'desertification_proxy is not null',
            'desertification_proxy is not null'
        ) }} as desertification_status
    from {{ source('gold', 'fact_climate_indicator_daily') }}
),
vegetation as (
    select aoi_key, date_key, ndvi_mean, evi_mean
    from {{ source('gold', 'fact_vegetation_health_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
)
select
    c.aoi_key,
    a.aoi_name,
    a.region,
    c.date_key,
    c.lst_c,
    c.lst_anomaly_c,
    c.sst_c,
    c.sst_anomaly_c,
    v.ndvi_mean,
    v.evi_mean,
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
    {{ decided_flag('c.warming_status') }}                as warming_flag,
    c.warming_status,
    {{ decided_flag('c.desertification_status') }}        as desertification_flag,
    c.desertification_status,
    a.area_km2
from clim c
left join vegetation v
    on c.aoi_key = v.aoi_key and c.date_key = v.date_key
left join aoi a on c.aoi_key = a.aoi_key
