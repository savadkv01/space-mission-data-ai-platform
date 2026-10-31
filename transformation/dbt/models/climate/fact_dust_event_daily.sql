-- Gold: Dust-Event Analytics (Phase 9b) -> fact_dust_event_daily (1 row/AOI/day).
-- Mirrors transformation.batch.climate_silver_to_gold.gold_dust_event_daily. AOD
-- rows already carry aoi_id from Bronze, so the aggregation is pure SQL. The UV
-- aerosol index is denormalized from the TROPOMI AER_AI column; corridor_aod_max
-- is the maximum AOD across other AOIs on the same day. NASA POWER wind is
-- joined from Silver by AOI and date; it is point context at the AOI centroid.
with aerosol as (
    select
        aoi_id                as aoi_key,
        stat_date             as date_key,
        aod_550nm,
        uv_aerosol_index,
        valid_fraction
    from {{ source('silver_climate', 'silver_aerosol') }}
    where aoi_id is not null
),
agg_aer as (
    select
        aoi_key,
        date_key,
        avg(aod_550nm)         as aod_mean,
        max(aod_550nm)         as aod_max,
        avg(uv_aerosol_index)  as uv_from_aer,
        avg(valid_fraction)    as valid_fraction
    from aerosol
    group by aoi_key, date_key
),
aer_ai as (
    select
        aoi_id       as aoi_key,
        stat_date    as date_key,
        avg(mean)    as uv_from_col
    from {{ source('silver_climate', 'silver_atmos_column') }}
    where gas_code = 'AER_AI' and aoi_id is not null
    group by aoi_id, stat_date
),
wind as (
    select
        aoi_id as aoi_key,
        stat_date as date_key,
        max(case when parameter = 'WS2M' then value_std end) as wind_speed_mean,
        max(case when parameter = 'WD2M' then value_std end) as wind_dir_dominant
    from {{ source('silver_climate', 'silver_wind') }}
    where quality_flag = 'valid'
    group by aoi_id, stat_date
),
joined as (
    select
        a.aoi_key,
        a.date_key,
        a.aod_mean,
        a.aod_max,
        coalesce(a.uv_from_aer, ai.uv_from_col) as uv_aerosol_index_mean,
        a.valid_fraction,
        (
            select max(other.aod_mean)
            from agg_aer other
            where other.date_key = a.date_key and other.aoi_key <> a.aoi_key
        ) as corridor_aod_max,
        w.wind_speed_mean,
        w.wind_dir_dominant
    from agg_aer a
    left join aer_ai ai
        on a.aoi_key = ai.aoi_key and a.date_key = ai.date_key
    left join wind w
        on a.aoi_key = w.aoi_key and a.date_key = w.date_key
)
select
    aoi_key,
    date_key,
    aod_mean,
    aod_max,
    uv_aerosol_index_mean,
    wind_speed_mean,
    wind_dir_dominant,
    corridor_aod_max,
    valid_fraction,
    case
        when aod_mean is null    then null
        when aod_mean < 0.2      then 0
        when aod_mean < 0.5      then 1
        when aod_mean < 1.0      then 2
        when aod_mean < 2.0      then 3
        else 4
    end as dust_severity_band,
    coalesce(aod_mean >= 0.5 and uv_aerosol_index_mean >= 1.0, false) as dust_flag,
    coalesce(corridor_aod_max >= 0.5 and wind_speed_mean > 0, false) as transport_flag
from joined
