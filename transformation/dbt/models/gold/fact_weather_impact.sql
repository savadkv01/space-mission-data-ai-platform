-- Gold: Space Weather Impact Analytics (Task 4.3) -> fact_weather_impact.
-- Daily correlation of geomagnetic activity with telemetry anomaly rate.
with weather as (
    select
        cast(event_ts as date) as date_key,
        kp_index,
        geomagnetic_storm
    from {{ source('silver', 'silver_space_weather') }}
),
weather_daily as (
    select
        date_key,
        max(kp_index)                                   as max_kp_index,
        avg(kp_index)                                   as mean_kp_index,
        sum(case when geomagnetic_storm then 1 else 0 end) as storm_events
    from weather
    group by date_key
),
telemetry_daily as (
    select
        date_key,
        count(*)                                                  as telemetry_samples,
        sum(case when anomaly_sensor_count > 0 or label_anomaly
                 then 1 else 0 end)                               as anomaly_samples
    from {{ ref('stg_telemetry') }}
    group by date_key
)
select
    coalesce(w.date_key, t.date_key)                    as date_key,
    round(w.max_kp_index, 2)                            as max_kp_index,
    round(w.mean_kp_index, 2)                           as mean_kp_index,
    coalesce(w.storm_events, 0)                         as storm_events,
    coalesce(t.telemetry_samples, 0)                    as telemetry_samples,
    coalesce(t.anomaly_samples, 0)                      as anomaly_samples,
    case when t.telemetry_samples > 0
         then round(t.anomaly_samples * 1.0 / t.telemetry_samples, 4) end as anomaly_rate
from weather_daily w
full outer join telemetry_daily t on w.date_key = t.date_key
