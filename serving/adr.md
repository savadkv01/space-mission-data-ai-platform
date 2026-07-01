# Serving Layer — Architecture Decision Records (Task 16)

Serving-layer ADRs use the `ADR-SV-*` prefix. They extend the platform ADRs
(architecture/14-adr.md) and data-modeling ADRs (ADR-06, ADR-09, ADR-10).

---

## ADR-SV-01 — Gold Layer is the only serving source

- **Status**: Accepted
- **Context**: Consumers could read Silver, Gold, or bespoke extracts. Mixed
  sources cause inconsistent, un-governed, and untrusted analytics.
- **Decision**: The serving layer reads **only** Gold marts. BI, APIs, ML, and RAG
  all consume serving products derived from Gold — never Silver or Bronze.
- **Consequences**: One trusted, quality-gated source; simpler lineage; a clear
  promotion boundary. Requires any new serving need to be expressed as a Gold mart
  first.
- **Alternatives**: Serve Silver for freshness (rejected — bypasses Gold quality
  gates and KPI curation).

---

## ADR-SV-02 — Materialized aggregates for dashboards

- **Status**: Accepted
- **Context**: Dashboards must meet a ≤2–3 s read SLA on a 16 GB laptop.
- **Decision**: Pre-compute cross-product daily rollups (`mv_kpi_platform_daily`,
  `mv_catalog_quality`) and rebuild them after Gold; dashboards read the aggregates.
- **Consequences**: Fast, cheap dashboard reads; daily-bounded staleness (aligned
  with batch EO freshness). Adds a refresh + cache-invalidation step.
- **Alternatives**: Live aggregation per request (rejected — latency + repeated cost).

---

## ADR-SV-03 — APIs are versioned (URI versioning)

- **Status**: Accepted
- **Context**: External consumers need a stable contract while the platform evolves.
- **Decision**: REST APIs are versioned in the URI (`/api/v1`). Breaking changes
  ship a new major version; old versions are retained ≥1 release with
  `Deprecation`/`Sunset` headers.
- **Consequences**: Backward compatibility and safe evolution; some duplication
  across versions during transition windows.
- **Alternatives**: Header/content negotiation versioning (rejected — less obvious
  to consumers); no versioning (rejected — breaks integrations).

---

## ADR-SV-04 — Full-rebuild serving refresh at MVP scale

- **Status**: Accepted
- **Context**: Serving products can be refreshed incrementally or fully rebuilt.
- **Decision**: At MVP grain (AOI/day, scene, vessel/day) products are small, so
  the refresh **fully rebuilds** serving tables after Gold — simpler and correct.
- **Consequences**: No incremental-merge complexity or drift; trivial to reason
  about. Revisit with dbt incremental models when volumes grow.
- **Alternatives**: Incremental merge now (rejected — premature complexity for the
  data volume).

---

## ADR-SV-05 — Wide denormalized data products

- **Status**: Accepted
- **Context**: Serving models can be normalized (star) or denormalized (wide).
- **Decision**: Serving products are **wide** — Gold dimensions (e.g. AOI name,
  area, corroboration) are pre-joined so BI/API rows are self-describing with no
  runtime joins.
- **Consequences**: Fast reads, simple consumers, easy caching; modest storage
  duplication. Star schemas remain upstream in Gold for modeling integrity.
- **Alternatives**: Serve normalized star schemas (rejected — runtime join cost
  and analyst complexity on the read path).

---

## ADR-SV-06 — Semantic layer is required (single-sourced metrics)

- **Status**: Accepted
- **Context**: The same KPI was at risk of being computed differently in BI, API,
  and RAG, causing metric drift and lost trust.
- **Decision**: All metrics are defined once in `serving.marts.semantic.METRICS`
  and consumed everywhere; requesting an unknown metric fails fast.
- **Consequences**: Consistent KPIs across every surface; a single review point for
  metric changes. All consumers must route KPI math through the semantic layer.
- **Alternatives**: Per-consumer metric SQL (rejected — drift, duplication,
  reconciliation incidents — see I-04, I-11).

---

## ADR-SV-07 — Data products are defined, owned, and SLA-bound

- **Status**: Accepted
- **Context**: Un-owned datasets rot; consumers can't tell what is trustworthy.
- **Decision**: Every serving dataset is a **data product** with an owner,
  consumers, refresh cadence, SLA, source lineage, and KPIs (see `products/`).
- **Consequences**: Discoverability, accountability, and measurable SLAs; a small
  documentation/governance overhead per product.
- **Alternatives**: Ad-hoc serving tables (rejected — no ownership or trust model).
