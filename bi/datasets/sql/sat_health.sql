-- Certified dataset: sat_health  (Superset virtual dataset)  [SIMULATION-TRACK]
-- Owner: Platform Lead  |  Grain: satellite / day  |  Track: sim (post-MVP, ADR-09)
-- Source: Gold mart fact_sat_health (synthetic telemetry). No dbt serving product
-- exists for the sim track, so this certified SQL reads the Gold Parquet directly
-- via DuckDB httpfs and applies the SAME status band the serving semantic layer
-- defines (>=0.8 nominal, >=0.5 degraded, else critical).
--
-- Superset database connection: `serving_duckdb`  (S3 creds set on the connection)
-- NOTE: clearly labelled `sim` in every chart title — not a real-data KPI.
select
    sat_key,
    cast(date_key as date)          as health_date,
    samples,
    health_score,
    anomaly_samples,
    labelled_anomalies,
    anomaly_density,
    battery_voltage_drift,
    case
        when health_score is null then 'unknown'
        when health_score >= 0.8  then 'nominal'
        when health_score >= 0.5  then 'degraded'
        else 'critical'
    end                             as status
from read_parquet('s3://gold/fact_sat_health/*.parquet')
