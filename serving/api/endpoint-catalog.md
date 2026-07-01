# Endpoint Catalog (Task 5)

All endpoints are versioned under `/api/v1`, read-only, and backed by serving
products. `sim` endpoints serve Simulation-Track data and are gated behind a
`demo` scope.

## MVP Earth-Observation Endpoints

| Method | Path | Product | Purpose |
| --- | --- | --- | --- |
| GET | `/api/v1/analytics/wildfire` | `serving_wildfire_daily` | Wildfire activity by AOI/day |
| GET | `/api/v1/analytics/flood` | `serving_flood_daily` | Flood extent by AOI/day |
| GET | `/api/v1/vessels` | `serving_vessel_activity` | Vessel activity + triage |
| GET | `/api/v1/vessels/{vessel_key}` | `serving_vessel_activity` | Single vessel history |
| GET | `/api/v1/scenes` | `serving_scene_catalog` | Imagery catalog search |
| GET | `/api/v1/scenes/{scene_key}` | `serving_scene_catalog` | Single scene metadata |
| GET | `/api/v1/analytics/validation` | `serving_aoi_validation` | EMS corroboration / QA |
| GET | `/api/v1/analytics/platform-daily` | `mv_kpi_platform_daily` | Executive daily rollup |
| GET | `/api/v1/aois` | `dim_aoi` | AOI dimension lookup |

## Simulation-Track Endpoints (`demo` scope)

| Method | Path | Product | Purpose |
| --- | --- | --- | --- |
| GET | `/api/v1/satellites` | `serving_sat_health` | Satellite health (sim) |
| GET | `/api/v1/satellites/{sat_key}` | `serving_sat_health` | Single satellite (sim) |
| GET | `/api/v1/missions` | `serving_mission_status` | Mission status (sim/planned) |
| GET | `/api/v1/launches` | `serving_launch_monthly` | Launch performance (sim) |
| GET | `/api/v1/telemetry` | `stream_sat_health_1m` | Streaming telemetry (sim) |
| GET | `/api/v1/weather` | `serving_weather_impact` | Space weather (sim) |

## Common Query Parameters

| Param | Applies to | Notes |
| --- | --- | --- |
| `limit`, `cursor` | list endpoints | pagination (default 50, max 500) |
| `date_from`, `date_to` | daily products | inclusive UTC date range |
| `aoi_key` | wildfire, flood, validation | filter by AOI |
| `severity` | wildfire | `extreme\|high\|moderate\|low` |
| `flood_flag` | flood | boolean |
| `suspicious` | vessels | boolean |
| `searchable`, `provider`, `q` | scenes | search/filter |
| `event_type` | validation | `fire\|flood` |

## Example

```
GET /api/v1/analytics/wildfire?aoi_key=EMS-A&date_from=2026-06-01&severity=extreme&limit=20
Authorization: Bearer <token>

200 OK
{
  "data": [
    { "aoi_key": "EMS-A", "aoi_name": "Attica Fire", "date_key": "2026-06-03",
      "detections": 47, "max_frp": 180.0, "severity": "extreme", "ems_corroborated": true }
  ],
  "meta": { "count": 1, "next_cursor": null, "generated_at": "2026-07-01T00:00:00Z" }
}
```

## Health & Ops Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/healthz` | liveness |
| GET | `/readyz` | serving store reachable + freshness within SLA |
| GET | `/metrics` | Prometheus metrics (latency, cache hits) |
