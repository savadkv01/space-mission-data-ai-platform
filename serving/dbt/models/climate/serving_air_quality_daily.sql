-- Serving data product: Air Quality. Mirrors
-- serving.marts.climate.climate_products.serve_air_quality_daily. Wide,
-- business-named, and pre-joined to dim_aoi so BI/API read with no runtime joins.
with aq as (
    select * from {{ source('gold', 'fact_air_quality_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
)
select
    q.aoi_key,
    a.aoi_name,
    q.date_key,
    q.pm25_mean,
    q.pm25_max,
    q.pm10_mean,
    q.pm10_max,
    q.no2_column_mean,
    q.so2_column_mean,
    q.co_column_mean,
    q.o3_column_mean,
    q.station_count,
    q.aqi_pm25,
    q.aqi_pm10,
    q.aqi_band,
    q.exceedance_flag,
    a.area_km2
from aq q
left join aoi a on q.aoi_key = a.aoi_key
