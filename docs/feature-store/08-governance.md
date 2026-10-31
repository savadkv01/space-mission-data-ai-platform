# 08 — Governance and Lifecycle

## Ownership

| Asset | Accountable owner | Required review |
|---|---|---|
| Source meaning and business grain | Upstream data product owner | Document source, units, time/spatial coverage, and exclusions |
| Feature definition and transforms | Feature steward | Types, null policy, TTL, lineage, tests, and consumers |
| Readiness status | Data owner + quality steward | Evidence and explicitly permitted use |
| PostgreSQL runtime and backups | Platform operator | Capacity, restore, access, and retention |
| Training dataset manifest | Consuming ML engineer | Label lineage, PIT semantics, version and split |

## Lineage and classification

Each source feature record retains its source reference, feature event date,
data nature, and readiness status. The feature catalog identifies the source
Gold table and known limitation. Use `open_source_derived_catalog`,
`synthetic_demo`, and other nature labels precisely; do not infer a real-world
classification from registration.

## Versioning and deprecation

- A feature's name, entity key, units, grain, and interpretation form its
  consumer contract.
- Non-breaking additions require schema, quality, and consumer tests.
- A breaking semantic/unit/grain change creates a new view name/version; do not
  silently reinterpret a registered feature.
- Deprecation sequence: mark deprecated in the catalog, identify consumers,
  provide a migration window, remove from feature services, then remove the
  registry definition and online table after backup/approval.
- Training outputs include a content-addressed dataset version and manifest.

## Access and secrets

Reuse the platform's PostgreSQL and MinIO credentials from the ignored local
environment file. Never put credentials in the repository or return them from
readiness endpoints. The job token is optional at startup but required to
enable internal materialization calls.
