# 12 — Quality SLAs & KPIs

> Summary of the measurable targets. Full tables and per-use-case KPIs:
> [quality/monitoring/quality-kpis.md](../../quality/monitoring/quality-kpis.md).

---

## 1. Platform KPIs

| KPI | Target | Alert |
|-----|--------|-------|
| Pipeline success rate | ≥ 99% | < 95% |
| Validation pass rate | ≥ 99.5% | < 98% |
| Data completeness % | ≥ 99% | < 97% |
| Duplicate % | ≤ 0.1% | > 0.5% |
| Freshness SLA adherence | ≥ 98% | < 95% |
| Quarantine rate | ≤ 1% | > 2% |
| MTTD | ≤ 15 min | > 30 min |
| MTTR | ≤ 4 h | > 8 h |

## 2. Freshness SLAs

| Entity | SLA | Driver |
|--------|-----|--------|
| `silver_fire` | ≤ 6 h | UC-15 detection latency |
| `silver_index` | ≤ 48 h | UC-16 flood assessment |
| `silver_vessel` | ≤ 24 h | UC-18 triage |
| `silver_scene` | ≤ 12 h | UC-25 catalog currency |

## 3. Per-use-case KPIs

| Use case | Quality KPI | Target |
|----------|-------------|--------|
| UC-15 wildfire | detection completeness | ≥ 99% |
| UC-16 flood | valid-pixel coverage | ≥ 50% |
| UC-18 fishing | identity completeness | ≥ 80% |
| UC-25 catalog | mean `completeness_score` | ≥ 0.8 |
| UC-27 damage | pre/post scene pairing | ≥ 95% |
| UC-14 change | index continuity | ≥ 90% |

## 4. SLA response matrix

| Severity | Detect | Acknowledge | Recover |
|----------|--------|-------------|---------|
| Critical | ≤ 15 min | ≤ 30 min | ≤ 4 h |
| High | ≤ 30 min | ≤ 1 h | ≤ 8 h |
| Medium | ≤ 1 h | ≤ 4 h | next business day |
| Low | daily profile | — | backlog |

## 5. Measurement

Every KPI derives from the Prometheus metrics in [08-monitoring.md](08-monitoring.md):

- Validation pass rate = `1 − failures/validated`
- Duplicate % = `dq_duplicate_ratio`
- Completeness % = `1 − dq_null_pct` on mandatory columns
- Freshness adherence = share within `dq_freshness_lag_seconds ≤ SLA`
- MTTD/MTTR = Alertmanager + incident timestamps

KPIs are reviewed weekly and reported on the Grafana **Quality Overview**
dashboard. Targets are laptop-realistic (single-node, batch-first, 16 GB RAM).
