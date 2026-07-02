# BI Governance Documentation

> **Phase 12 — Business Intelligence & Analytics** · Governance & design narrative

These 14 documents are the enterprise governance narrative for the BI layer. The
implementation (certified SQL, Superset YAML exports) lives in [`../../bi/`](../../bi/).

| # | Document | Task |
| --- | --- | --- |
| 01 | [Strategy](./01-strategy.md) | BI vision, self-service, KPI governance, lifecycle |
| 02 | [Dashboard Catalog](./02-dashboard-catalog.md) | Hierarchy + index of the 6 dashboards |
| 03 | [KPIs](./03-kpis.md) | KPI governance + KPI→dashboard matrix |
| 04 | [Dashboard Standards](./04-dashboard-standards.md) | Layout, filters, accessibility, colour, sim-labelling |
| 05 | [User Personas](./05-user-personas.md) | Persona→role→access matrix |
| 06 | [Datasets](./06-datasets.md) | Dataset tiers, lifecycle, ownership |
| 07 | [Reporting](./07-reporting.md) | Scheduled + real-time reporting governance |
| 08 | [Alerting](./08-alerting.md) | Decision + infra alert planes |
| 09 | [Performance](./09-performance.md) | Caching, materialized views, 16 GB discipline |
| 10 | [Security](./10-security.md) | RBAC, RLS, permissions, audit, OWASP |
| 11 | [Production Incidents](./11-production-incidents.md) | 12 incident scenarios |
| 12 | [Trade-offs](./12-trade-offs.md) | Live/cached, materialized/direct, self-service/governed |
| 13 | [ADR](./13-adr.md) | 7 architecture decision records |
| 14 | [Glossary](./14-glossary.md) | BI terms |

## Key Alignment

- **MVP-first**: Earth Observation / maritime dashboards are primary; spacecraft
  satellite/launch/weather are `sim` demonstrators isolated to the `demo` role
  (ADR-09, ADR-BI-06).
- **One truth**: KPIs single-sourced in the serving semantic layer (ADR-BI-02).
- **Governed self-service**: explore freely, publish only certified assets
  (ADR-BI-03).
