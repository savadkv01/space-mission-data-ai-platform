# Platform Operations Dashboard

> Phase 12 · Task 2 — Dashboard Catalog · Audience: **Data Engineers, Platform
> Engineers** · Superset slug: `platform` · Roles: `steward`, `ai`, `exec` (read)

## Purpose

Operational health of the data platform itself: are pipelines succeeding, is data
fresh, are jobs failing, and is the serving layer meeting its latency SLA. This
dashboard blends the certified catalog-quality aggregate with **observability
metrics** exposed by Prometheus/Grafana and the Airflow DAG state.

## KPI Tiles

| Tile | KPI | Source | Definition | Threshold |
| --- | --- | --- | --- | --- |
| Pipeline Success | DAG success rate | Airflow / Prometheus | % task-runs successful (24h) | ≥0.98 |
| Data Freshness | Gold lag | serving refresh metric | minutes since last Gold write | ≤60 min |
| Processing Latency | serving refresh duration | Airflow run duration | p95 DAG duration | ≤ SLA |
| Failed Jobs | failures (24h) | Airflow | count of failed task-runs | 0 |
| Resource Usage | container mem/cpu | Prometheus / cAdvisor | peak mem vs limit | <90% |
| Searchable Rate | catalog searchable rate | `catalog_quality.searchable_rate` | share of scenes searchable | ≥0.9 |

> Data-quality/observability metrics come from the platform observability stack
> (Prometheus + Grafana + OTel, see
> [../../architecture/08-observability-architecture.md](../../architecture/08-observability-architecture.md)).
> Superset renders the analytics view; Grafana remains the low-level infra view.

## Charts

| Chart | Type | Dataset · source |
| --- | --- | --- |
| DAG success rate (trend) | line | Prometheus (airflow exporter) |
| Data freshness by layer | bar | serving refresh metrics |
| Failed jobs by DAG | table | Airflow metadata |
| Catalog quality by collection | bar | `catalog_quality` |
| Completeness vs cloud cover | scatter | `catalog_quality` |
| Resource usage by service | heatmap | Prometheus |

## Layout (wireframe)

```
+---------------------------------------------------------------+
| PLATFORM OPERATIONS                                     [ ▾ ]  |
+---------+---------+---------+---------+---------+---------+
| Pipeline| Data    | Latency | Failed  | Resource| Search  |
| Success | Fresh   | p95     | Jobs    | Usage   | Rate    |
|  99.1%  | 12 min  | 4.2 min |   0     |  71%    |  0.94   |
+---------+---------+---------+---------+---------+---------+
| DAG success rate (trend)      | Failed jobs by DAG (table)    |
+-------------------------------+-------------------------------+
| Catalog quality by collection | Completeness vs cloud cover   |
+-------------------------------+-------------------------------+
```

## Filters

- Time range (default 24h for ops, 7d for trend charts).
- Service / DAG selector.

## Drill-down

- Failed job row → Airflow UI link (external).
- Catalog quality bar → **Earth Observation Dashboard** imagery tab.

## Alignment

- Serves KPIs Pipeline Success, Data Freshness, Processing Latency from
  [../../docs/business/08-kpis.md](../../docs/business/08-kpis.md).
- Observability contract:
  [../../architecture/08-observability-architecture.md](../../architecture/08-observability-architecture.md)
  and [../../serving/monitoring.md](../../serving/monitoring.md).
