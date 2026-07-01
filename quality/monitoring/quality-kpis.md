# Data Quality KPIs & SLAs

> Measurable targets for the platform. Thresholds are laptop-realistic
> (single-node, batch-first) and align with the MVP business KPIs in
> [docs/business/08-kpis.md](../../docs/business/08-kpis.md).

---

## 1. Platform quality KPIs

| KPI | Definition | Target | Alert threshold |
|-----|------------|--------|-----------------|
| Pipeline success rate | successful runs / total runs | ≥ 99% | < 95% |
| Validation pass rate | valid records / validated records | ≥ 99.5% | < 98% |
| Data completeness % | non-null mandatory fields / expected | ≥ 99% | < 97% |
| Duplicate % | duplicates / total (post-dedup) | ≤ 0.1% | > 0.5% |
| Freshness SLA adherence | batches within freshness SLA | ≥ 98% | < 95% |
| Quarantine rate | quarantined / ingested | ≤ 1% | > 2% |
| Mean Time To Detect (MTTD) | issue occurs → alert fires | ≤ 15 min | > 30 min |
| Mean Time To Recover (MTTR) | alert → data restored/certified | ≤ 4 h | > 8 h |
| Schema stability | days between breaking schema changes | ≥ 30 | < 7 |

---

## 2. Freshness SLAs by dataset

| Entity | Source cadence | Freshness SLA | Rationale |
|--------|----------------|---------------|-----------|
| `silver_fire` | FIRMS ~3–5 near-real-time passes/day | ≤ 6 h | UC-15 detection latency |
| `silver_index` | Sentinel-2 ~5-day revisit | ≤ 48 h | UC-16 flood assessment |
| `silver_vessel` | GFW identity (slow-changing) | ≤ 24 h | UC-18 triage cycle |
| `silver_scene` | STAC/CMR continuous | ≤ 12 h | UC-25 catalog currency |
| `ref_aoi` | Copernicus EMS (manual) | on activation | ground-truth layer |

---

## 3. Per-use-case quality KPIs

| Use case | Quality KPI | Target |
|----------|-------------|--------|
| UC-15 wildfire | detection completeness (no dropped granules) | ≥ 99% |
| UC-16 flood | valid-pixel coverage on classified AOIs | ≥ 50% |
| UC-18 fishing | vessel identity completeness (flag+imo) | ≥ 80% |
| UC-25 catalog | scene `completeness_score` mean | ≥ 0.8 |
| UC-27 damage | pre/post scene pairing availability | ≥ 95% |
| UC-14 change | index time-series continuity | ≥ 90% |

---

## 4. SLA response matrix

| Severity | Example | Detect | Acknowledge | Recover |
|----------|---------|--------|-------------|---------|
| Critical | freshness breach, checkpoint fail, schema change | ≤ 15 min | ≤ 30 min | ≤ 4 h |
| High | quarantine flood, null spike | ≤ 30 min | ≤ 1 h | ≤ 8 h |
| Medium | duplicate spike, drift warn | ≤ 1 h | ≤ 4 h | next business day |
| Low | cosmetic metadata gap | daily profile | — | backlog |

---

## 5. Measurement source

Every KPI is derived from the Prometheus metrics in
[monitoring-strategy.md](monitoring-strategy.md):

- Validation pass rate = `1 − dq_validation_failures_total / dq_records_validated_total`
- Duplicate % = `dq_duplicate_ratio`
- Completeness % = `1 − dq_null_pct` on mandatory columns
- Freshness adherence = share of `dq_freshness_lag_seconds ≤ SLA`
- MTTD / MTTR = Alertmanager + incident timestamps

KPIs are reviewed weekly by the data steward and reported on the Grafana
**Quality Overview** dashboard.
