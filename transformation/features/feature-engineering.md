# Design — Feature Engineering

> Code: [feature_engineering.py](feature_engineering.py) · Spec: [docs/transformation/08-feature-engineering.md](../../docs/transformation/08-feature-engineering.md)

## Principles

- Derive from **Silver** (inherits cleaning/dedup) → deterministic, windowed → no train/serve skew.
- One feature dataset keyed by `(entity_id, event_ts, feature_namespace)`; reused across models.

## Functions

| Function | Namespace | Source |
| --- | --- | --- |
| `satellite_health_features` | `sat_health` | silver_telemetry |
| `orbit_features` | `orbit` | silver_orbit |
| `space_weather_features` | `space_weather` | silver_space_weather |

See [feature-definitions.md](feature-definitions.md) for the full feature table.

## Reuse

Namespacing enables selective reads; the same Spark job can emit Silver + features in one pass (ADR-5). Recomputable for backfill and online inference identically.
