# Design — Silver → Gold (batch)

> Code: [silver_to_gold.py](silver_to_gold.py) · dbt: [../dbt/models/gold/](../dbt/models/gold/) · Spec: [docs/transformation/04-silver-gold.md](../../docs/transformation/04-silver-gold.md)

## Gold marts

| Mart | Function | Grain | dbt model |
| --- | --- | --- | --- |
| Satellite Health | `gold_satellite_health` | sat / day | `fact_sat_health.sql` |
| Launch Performance | `gold_launch_performance` | provider / month | — |
| Space Weather Impact | `gold_space_weather_impact` | day | `fact_weather_impact.sql` |
| Earth Observation | `gold_earth_observation` | geo_key / day | — |

## KPI definitions (single source)

- `health_score = mean(health_weight) × (1 − 0.5·anomaly_density)`
- `anomaly_rate = anomaly_samples / telemetry_samples`
- `success_rate = successes / launches`

The Python functions and dbt SQL implement identical KPI math; dbt tests enforce grain uniqueness and value ranges (`accepted_range` 0–1).

## Why two implementations

Pure-Python = offline/laptop + unit tests. dbt SQL = production Gold with lineage + tests. Shared test cases keep them in sync (see ADR-2).
