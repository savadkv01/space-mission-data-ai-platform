# Orbit Data — Data Quality Rules

> **Track:** Simulation (post-MVP). Orbit positions are propagated from TLE
> elements / synthetic generation and retained for the streaming demonstrator
> (ADR-09). Not on the MVP critical path.

Entity: `silver_orbit` (natural key `satellite_id`, `event_ts`).

---

## Mandatory fields

| Field | Type | Rule |
|-------|------|------|
| `event_ts` | ISO-8601 UTC | Non-null, parseable |
| `satellite_id` | string | Non-null |
| `latitude` | float | `-90 ≤ lat ≤ 90` |
| `longitude` | float | `-180 ≤ lon ≤ 180` (normalized via `normalize_lon`) |
| `altitude_km` | float | `0 ≤ alt ≤ 50000` |
| `geo_key` | string | Non-null, consistent with (lat, lon) |

## Optional fields

| Field | Type | Rule |
|-------|------|------|
| `propagator` | string | Default `unknown`; controlled vocabulary |

## Accepted ranges

| Signal | Range | Notes |
|--------|-------|-------|
| Latitude | `[-90, 90]` | Hard bound |
| Longitude | `[-180, 180]` | Normalized |
| Altitude (km) | `[0, 50000]` | LEO → GEO+ envelope |

## Referential integrity, duplicates, timestamp, geospatial

- **Duplicate rule:** `(satellite_id, event_ts)` unique after dedup.
- **Timestamp rule:** orbit timestamps per satellite must increase
  chronologically (monotonic); regressions rejected/quarantined.
- **Geospatial rule:** lat/lon within earth bounds; `geo_key` must match the
  point grid cell.
- **Physical plausibility:** successive positions must not imply velocities
  beyond orbital limits (coarse jump check — warn severity).

**Business impact of failure:** invalid positions corrupt any downstream
geospatial join and mislead ground-track visualizations.
