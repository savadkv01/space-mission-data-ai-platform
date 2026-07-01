# Space Weather — Data Quality Rules

> **Track:** Simulation (post-MVP). Space-weather events (NOAA SWPC-shaped) feed
> the space-weather-impact demonstrator and correlate with telemetry anomalies.
> Retained for realism, not on the MVP critical path (ADR-09).

Entity: `silver_space_weather` (natural key `event_ts`, `event_type`).

---

## Mandatory fields

| Field | Type | Rule |
|-------|------|------|
| `event_ts` | ISO-8601 UTC | Non-null, parseable |
| `event_type` | string | Non-null (default `space_weather`) |
| `kp_index` | float | `0 ≤ kp ≤ 9` |

## Optional fields

| Field | Type | Rule |
|-------|------|------|
| `flare_letter` | char | `∈ {A, B, C, M, X}` |
| `flare_class` | string | Pattern `[ABCMX][0-9](\.[0-9])?` (e.g. `M3`, `X1.5`) |
| `geomagnetic_storm` | bool | `true` iff `kp_index ≥ 5.0` |
| `severity` | string | `∈ {quiet, G1, G2, G3, G4, G5}` |
| `source` | string | Default `unknown` |

## Accepted ranges

| Signal | Range | Notes |
|--------|-------|-------|
| `kp_index` | `[0, 9]` | Planetary K-index |
| Flare class magnitude | `[0.0, 9.9]` × letter | Logarithmic X-ray flux |

## Referential integrity, duplicates, timestamp, geospatial

- **Duplicate rule:** `(event_ts, event_type)` unique after dedup.
- **Timestamp rule:** every weather event requires a valid, parseable
  `event_ts`; events without timestamps are quarantined.
- **Consistency rule:** `geomagnetic_storm` must agree with the `kp_index ≥ 5.0`
  threshold; `severity` band must match `kp_index`.
- **Geospatial:** N/A (global index).

**Business impact of failure:** mis-scaled Kp values break the storm-to-anomaly
correlation that underpins the space-weather-impact analytics.
