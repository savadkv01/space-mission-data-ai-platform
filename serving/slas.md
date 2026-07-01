# Serving SLAs (Task 11)

Measurable targets for the serving layer. These are the contract consumers can
rely on; monitoring ([monitoring.md](monitoring.md)) alerts on breaches.

## Data Freshness

| Dataset | Freshness target | Measured as |
| --- | --- | --- |
| MVP daily products (wildfire/flood/vessel/scene/validation) | ≤ 24 h | now − max(`date_key` load time) |
| Platform daily rollup | ≤ 24 h + 30 min after products | rollup build timestamp |
| Simulation-Track (sim) | best-effort (demo) | n/a for production SLA |

## Dashboard Refresh

| Dashboard | Refresh SLA | Read latency (p95) |
| --- | --- | --- |
| Executive (materialized aggregate) | daily | ≤ 2 s |
| Operations (data products) | daily | ≤ 3 s |
| Engineering (catalog quality) | daily | ≤ 3 s |

## API Latency

| Endpoint class | p50 | p95 | p99 |
| --- | --- | --- | --- |
| Single-entity (`/scenes/{id}`) | ≤ 80 ms | ≤ 300 ms | ≤ 600 ms |
| List/analytics (paged) | ≤ 150 ms | ≤ 400 ms | ≤ 800 ms |
| Search (`/scenes?q=`) | ≤ 200 ms | ≤ 500 ms | ≤ 1 s |

## Availability

| Component | Target |
| --- | --- |
| Serving API | 99.5 % monthly |
| BI (Superset) | 99.0 % monthly |
| Serving store (DuckDB/lakehouse) | 99.5 % monthly |

## Query Performance

| Query type | Target |
| --- | --- |
| Data-product full scan | ≤ 1 s |
| Materialized aggregate read | ≤ 200 ms |
| Cache hit ratio (API) | ≥ 70 % |

## SLA Governance

- Breaches raise alerts and are triaged via [incidents.md](incidents.md).
- Freshness beyond SLA returns `503` from `/readyz` (serving marked not-ready).
- Simulation-Track products carry **no production SLA** and are excluded from
  availability accounting.
