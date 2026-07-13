# BI Dataset Governance

> Phase 12 — Business Intelligence & Analytics · Task 6 / Task 10

Governance rules that keep the BI layer trustworthy, reproducible, and aligned
with the serving contract. These rules are enforced in code review and in the
`serving_refresh` DAG, not by convention alone.

## Golden Rules

1. **No ad-hoc SQL in charts.** Every chart selects columns from a certified
   dataset. KPI logic lives in the serving product / semantic layer.
2. **BI never touches Silver or Gold directly** — except the three `sim`
   datasets, which have no serving product and are read-only demonstrators.
3. **One dataset per serving product.** Datasets are thin; joins are pre-computed
   upstream so BI has zero runtime joins.
4. **Metrics are certified, not calculated.** Severity, quality band, trust,
   status, and storm-day bands are pre-computed upstream; BI displays them.
5. **Version control is the source of truth.** Superset assets are exported to
   [`../superset/`](../superset/) and imported from there — the UI is never the
   canonical definition.

## Change Management

| Change | Required approval | Test gate |
| --- | --- | --- |
| New certified dataset | Product owner + BI lead | serving dbt contract tests green |
| Column added to a dataset | Dataset owner | dataset SQL compiles; chart smoke test |
| KPI formula change | Data governance council | semantic-layer test + API parity test |
| Dashboard published to `exec` | BI lead | design-standards checklist |
| Dataset deprecation | Product owner | 1-release notice + downstream chart audit |

## Certification Checklist

A dataset is **Certified** only when all are true:

- [ ] SQL committed under `bi/datasets/sql/` with owner + grain header.
- [ ] Source serving product passes its dbt tests (grain uniqueness, KPI bounds,
      accepted band values).
- [ ] Column names are business-friendly and match the serving contract.
- [ ] Sensitivity tag inherited from [`serving/access-strategy.md`](../../serving/access-strategy.md).
- [ ] Role grants defined (see [`../../serving/security.md`](../../serving/security.md)).
- [ ] Refresh + cache TTL documented in [certified-datasets.md](./certified-datasets.md).

## Data Freshness & Refresh Governance

| Dataset class | Freshness SLO | Cache TTL | Refresh trigger |
| --- | --- | --- | --- |
| Materialized aggregate (`platform_daily`, `climate_daily`) | ≤ 15 min behind serving | 15 min | `serving_refresh` DAG completion |
| Daily serving product | ≤ 1 h behind Gold | 1 h | `serving_refresh` DAG completion |
| Sim-track (`gold.*`) | best-effort (demo) | 1 h | Gold write |

Cache is warmed after — never before — the serving refresh completes, so a
dashboard never shows a half-built product (see
[incident BI-04](../docs/bi/11-production-incidents.md)).

## Phase 12b Climate Extension

The five Phase 12b climate datasets (`air_quality_daily`, `dust_event_daily`,
`climate_indicator_daily`, `vegetation_health_daily`, `climate_daily`) inherit
this governance unchanged — no new rules, tooling, or ownership model:

- They read certified 11b serving products (`serving.serving_*` /
  `serving_agg.mv_kpi_climate_daily`), never Silver/Gold directly.
- Grain uniqueness + KPI bounds + accepted-band values are enforced by the 11b
  dbt contract tests ([`serving/dbt/models/climate/_climate.yml`](../../serving/dbt/models/climate/_climate.yml)).
- No RLS is required (all climate AOIs are public); roles are `ops_airquality`,
  `ops_climate`, and `exec`.

## Auditability

- All dataset SQL changes are traceable via Git history.
- Superset query logs + `logs/` capture who ran what against which dataset.
- The KPI lineage (Gold → serving product → certified dataset → chart) is
  documented per KPI in [`../kpis/kpi-catalog.md`](../kpis/kpi-catalog.md).

## Quality Alignment

Dataset governance inherits, and does not duplicate, the platform data-quality
controls in [`quality/`](../../quality/):

- Grain and band correctness are enforced by serving dbt tests.
- Ownership is single-sourced in
  [`quality/governance/ownership-matrix.md`](../../quality/governance/ownership-matrix.md).
- BI incidents feed the same incident register format as
  [`quality/incidents/production-incidents.md`](../../quality/incidents/production-incidents.md).
