# 03 — KPIs

> Phase 12 · Task 3 — KPI Catalog

The full, per-KPI catalog (definition, formula, source tables, refresh, owner,
thresholds, business impact) is maintained in
[`bi/kpis/kpi-catalog.md`](../../bi/kpis/kpi-catalog.md). This document summarises
the governance model and the KPI-to-dashboard binding.

## Single Source of Truth

```mermaid
flowchart LR
    Sem["serving/marts/semantic.py<br/>METRICS (formula)"] --> KC["serving/semantic/kpi-catalog.md"]
    KC --> BIK["bi/kpis/kpi-catalog.md<br/>(binding: dataset, owner, threshold)"]
    BIK --> Tile["dashboard KPI tile"]
```

BI **binds** KPIs to datasets, owners, and thresholds; it never **defines** the
formula. The formula lives once, upstream.

## KPI → Dashboard Matrix

| KPI | Dataset | Dashboard(s) | Threshold (G/A/R) |
| --- | --- | --- | --- |
| Total Fire Detections | `platform_daily`/`wildfire_daily` | Executive, EO | trend |
| Mean Fire Radiative Power | `wildfire_daily` | EO | severity bands |
| Flood Day Rate | `flood_daily` | EO, Executive | trend |
| Suspicious Vessel Rate | `vessel_activity` | EO (maritime), Executive | any high → triage |
| Searchable Scene Rate | `catalog_quality` | Platform | ≥0.9 / 0.75–0.9 / <0.75 |
| EMS Corroboration Rate | `aoi_validation` | Executive, EO | ≥0.8 / 0.6–0.8 / <0.6 |
| Pipeline Success Rate | observability | Platform, Executive | ≥0.98 |
| Data Freshness | serving metric | Platform, Executive | ≤60 min |
| SLA Compliance | serving metric | Executive | ≥0.99 |
| Mean Satellite Health `sim` | `sat_health` | Satellite `sim` | ≥0.8 |
| Launch Success Rate `sim` | `launch_monthly` | Launch `sim` | ≥0.9 |
| Storm Days `sim` | `weather_impact` | Weather `sim` | ≥5 |

## Governance Rules

- A KPI reaches a dashboard only after it is registered in the semantic layer.
- Threshold changes are governance-council decisions (not analyst decisions).
- BI and API parity is asserted by the serving test suite; a divergence is a
  release blocker.

## Business Alignment

MVP KPI set mirrors [../../docs/business/08-kpis.md](../../docs/business/08-kpis.md)
(Mean Time to Detect, Alert Latency, False Negative Rate, Monitored Coverage,
Search Success Rate, Impact Assessment Turnaround), expressed through the
available EO/maritime data products.
