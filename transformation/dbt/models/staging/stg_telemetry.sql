-- Staging: cast + light rename of Silver telemetry for the Gold marts.
-- Silver already guarantees cleaning/dedup, so staging stays thin (Task 2).
with src as (
    select * from {{ source('silver', 'silver_telemetry') }}
)
select
    satellite_id                          as sat_key,
    cast(event_ts as timestamp)           as event_ts,
    cast(event_ts as date)                as date_key,
    health,
    coalesce(label_anomaly, false)        as label_anomaly,
    coalesce(anomaly_sensor_count, 0)     as anomaly_sensor_count,
    battery_voltage_value
from src
