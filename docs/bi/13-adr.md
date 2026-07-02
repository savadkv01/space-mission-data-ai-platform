# 13 — Architecture Decision Records

> Phase 12 · Task 13 — ADRs (≥5)

Format: Context · Decision · Alternatives · Consequences. Complements the platform
ADRs in [../../architecture/14-adr.md](../../architecture/14-adr.md) and the
serving ADRs in [../../serving/adr.md](../../serving/adr.md).

## ADR-BI-01 — Apache Superset as the BI tool
- **Context:** Need an enterprise-grade BI tool that runs on a 16 GB laptop with
  open-source licensing, RBAC/RLS, and version-controllable assets.
- **Decision:** Use **Apache Superset**, connecting to the serving DuckDB.
- **Alternatives:** Metabase (simpler, weaker RBAC/RLS + assets-as-code), Grafana
  (great for metrics, weak for tabular/BI), Power BI/Tableau (proprietary, cost,
  not laptop-open-source).
- **Consequences:** Rich charts, RBAC, RLS, YAML import/export; heavier than
  Metabase, mitigated by `mem_limit: 1g` + caching.

## ADR-BI-02 — Semantic layer as the single KPI source
- **Context:** BI, API, and RAG must never show divergent KPI values.
- **Decision:** All KPI formulas live in the serving **semantic layer**
  (`serving/marts/semantic.py`); BI displays, never re-derives.
- **Alternatives:** Superset calculated columns / metrics per chart (fast but
  divergent), duplicate SQL per dashboard.
- **Consequences:** Guaranteed consistency + API parity test; requires a PR to
  change a KPI (slower, intentional).

## ADR-BI-03 — Certified datasets only (no ad-hoc chart SQL)
- **Context:** Ad-hoc SQL in charts causes silent drift and unauditable numbers.
- **Decision:** One certified virtual dataset per serving product; charts select
  columns only. SQL is version-controlled in `bi/datasets/sql/`.
- **Alternatives:** Allow SQL Lab-backed charts on dashboards.
- **Consequences:** Full lineage + auditability; analysts must promote via PR.

## ADR-BI-04 — Dashboard design standards
- **Context:** Inconsistent dashboards reduce trust and accessibility.
- **Decision:** Enforce layout, colour, accessibility, time-filter, and sim-
  labelling standards ([04-dashboard-standards.md](./04-dashboard-standards.md))
  via a pre-publish checklist.
- **Alternatives:** Author discretion.
- **Consequences:** Consistent, accessible dashboards; a review gate per publish.

## ADR-BI-05 — Materialized aggregate for executive KPIs
- **Context:** Executive dashboards scanning wide products are slow on 16 GB.
- **Decision:** Back cross-product executive KPIs with the pre-computed
  `mv_kpi_platform_daily` materialized aggregate.
- **Alternatives:** Direct queries with heavy caching only.
- **Consequences:** Fast executive load within SLA; one extra rebuild step in the
  serving refresh DAG.

## ADR-BI-06 — Simulation-track dashboards isolated and labelled
- **Context:** Satellite/launch/weather run on synthetic data and are excluded
  from the MVP (ADR-09), but the prompt requires the six dashboards.
- **Decision:** Deliver sim dashboards, isolate them to the `demo` role, read Gold
  Parquet directly (no serving product), and hard-label every chart ` sim `.
- **Alternatives:** Omit them (violates the phase spec), or present them as
  first-class (misleads stakeholders).
- **Consequences:** Phase requirement met without compromising MVP trust; extra
  labelling discipline enforced by the design checklist.

## ADR-BI-07 — Superset assets-as-code
- **Context:** UI-authored dashboards aren't reproducible or reviewable.
- **Decision:** Export all Superset objects to YAML under `bi/superset/` and
  import from there; the UI is never the source of truth.
- **Alternatives:** Manual UI recreation, DB backup/restore.
- **Consequences:** Git-reviewable BI, reproducible from cold start; requires an
  export/import discipline (documented in the superset README).
