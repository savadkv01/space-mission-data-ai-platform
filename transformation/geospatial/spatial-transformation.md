# Spatial Transformation

> Code: [spatial_transform.py](spatial_transform.py) · Spec: [docs/transformation/10-geospatial.md](../../docs/transformation/10-geospatial.md)

## Primitives

| Function | Purpose |
| --- | --- |
| `normalize_lon` | wrap longitude into [-180, 180) |
| `clamp_lat` | clamp latitude to [-90, 90] |
| `snap_to_grid` | round to a 0.25° cell |
| `geo_key` | spatial key `grid_lat:grid_lon` |
| `haversine_km` | great-circle distance |
| `normalize_position` | adds `grid_lat/lon`, `geo_key`; wraps/clamps |
| `reconstruct_path_length_km` | sum great-circle segments of a ground track |

## Conventions

- Datum: WGS84 / EPSG:4326.
- Grid: 0.25° (~27 km at equator) — compact + join-friendly.

## Scale-out

`geo_key` equality joins degrade gracefully to **Spark + Apache Sedona** (H3/geohash) for true point/polygon joins at cluster scale — no schema change.
