# 12 — Trade-off Analysis

> Phase 12 · Task 12 — Trade-off Analysis

Each decision states the choice, alternatives, and trade-offs (per the platform
decision-transparency rule).

## Live dashboards vs cached dashboards

| Aspect | Live | Cached (chosen for most) |
| --- | --- | --- |
| Freshness | always current | up to TTL stale |
| Load / cost | scans on every view (bad on 16 GB) | cheap repeated views |
| UX latency | slow under load | fast |

**Decision:** **Cached** with TTL tied to the serving refresh (15 min aggregates,
1 h daily products). Real-time needs are met by **event alerts**, not by
constantly-live dashboards. Rationale: laptop resource limits + the serving refresh
is the true freshness boundary anyway.

## Materialized views vs direct queries

| Aspect | Materialized (`platform_daily`) | Direct query on wide products |
| --- | --- | --- |
| Executive latency | tiny scan, fast | scans every product |
| Storage | small extra table | none |
| Freshness | rebuilt per refresh | always as-built |

**Decision:** **Materialized** for executive/cross-product KPIs; **direct** for
operational drill-down where the product is already narrow. Trade-off: one extra
rebuild step in the refresh DAG, accepted for the latency SLA.

## Self-service BI vs governed BI

| Aspect | Self-service | Governed (chosen) |
| --- | --- | --- |
| Analyst freedom | high | high in SQL Lab, gated for dashboards |
| Consistency | risk of divergent KPIs | one certified truth |
| Speed to publish | instant | PR + review |

**Decision:** **Governed self-service** — free exploration in personal space,
promotion to dashboards only via certified datasets (PR + tests). Trade-off:
slower publish for a large gain in trust and BI/API parity.

## Operational dashboards vs executive dashboards

| Aspect | Operational | Executive |
| --- | --- | --- |
| Grain | row-level detail | aggregates |
| Latency tolerance | low (triage) | moderate |
| Audience | operators/engineers | leadership |
| Source | serving products | materialized aggregate |

**Decision:** **Both, separated by audience/role.** Operators get detail +
drill-through; executives get fast aggregates. Trade-off: more dashboards to
maintain, resolved by the shared certified dataset layer.

## MVP EO/maritime vs simulation-track dashboards

| Aspect | MVP (real data) | Sim track |
| --- | --- | --- |
| Business value | primary | demonstrator |
| Data realism | real open data | synthetic |
| Risk | trustworthy | must be labelled |

**Decision:** MVP dashboards are primary; sim dashboards are retained, isolated to
the `demo` role, and hard-labelled ` sim ` (ADR-09). Trade-off: extra labelling
discipline to avoid misrepresenting synthetic KPIs.

## BI tool: Superset vs alternatives

Recorded in [13-adr.md](./13-adr.md) (ADR-BI-01) and
[../../docs/infrastructure/12-trade-offs.md](../../docs/infrastructure/12-trade-offs.md):
Superset chosen for open-source, laptop-viability, RBAC/RLS, and assets-as-code.
