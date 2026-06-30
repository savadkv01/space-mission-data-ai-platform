-- Gold: Satellite Health Analytics (Task 4.1) -> fact_sat_health (1 row/sat/day).
-- Mirrors transformation.batch.silver_to_gold.gold_satellite_health so the SQL
-- and Spark paths produce the same KPI definition.
with t as (
    select * from {{ ref('stg_telemetry') }}
),
agg as (
    select
        sat_key,
        date_key,
        count(*)                                                   as samples,
        sum(case when anomaly_sensor_count > 0 then 1 else 0 end)  as anomaly_samples,
        sum(case when label_anomaly then 1 else 0 end)             as labelled_anomalies,
        avg(case
              when health = 'NOMINAL' then 1.0
              when health = 'ANOMALY' then 0.0
              else 0.5 end)                                        as base_score,
        max(battery_voltage_value) - min(battery_voltage_value)    as battery_voltage_drift
    from t
    group by sat_key, date_key
)
select
    sat_key,
    date_key,
    samples,
    anomaly_samples,
    labelled_anomalies,
    round(anomaly_samples * 1.0 / samples, 4)                       as anomaly_density,
    round(base_score * (1 - 0.5 * (anomaly_samples * 1.0 / samples)), 4) as health_score,
    round(battery_voltage_drift, 4)                                as battery_voltage_drift
from agg
