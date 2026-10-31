# 13 — Glossary

| Term | Definition |
|---|---|
| Analysis-ready | Product with reviewed grain, lineage, coverage, completeness, quality rules, and approved use. |
| Entity | Key used to join feature rows, such as a satellite, AOI, or scene. |
| Event timestamp | Time when the observation/feature applies; basis for point-in-time retrieval. |
| Feature view | Feast definition of a temporal feature set, its entity keys, source, schema, and TTL. |
| Feature service | Named group of feature views intended for a consumer contract. |
| Gold | Curated business layer; authoritative source for the feature-input bridge. |
| Materialization | Batch write of historical feature values into the online store. |
| Offline store | Historical source used to construct point-in-time training data. |
| Online store | Latest materialized feature values used by low-latency serving. |
| Point-in-time (PIT) join | Join that selects only feature values available at the entity event timestamp. |
| Readiness gate | Status-controlled rule that permits, restricts, or blocks materialization and online retrieval. |
| Registry | SQL-backed store of Feast entities, views, services, and materialization metadata. |
| Restricted | Narrow descriptive use allowed with explicit limitations; not a general analytical certification. |
| Synthetic demo | Generated test data used to verify workflow mechanics, not operational reality. |
| TTL | Feast feature-view time-to-live for historical retrieval; not a promise of online-row deletion. |
