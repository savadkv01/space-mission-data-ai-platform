# 12 — Architecture Decision Records

## ADR-FS-001 — Use Feast for feature definitions and retrieval

**Status:** Accepted  
**Decision:** Use open-source Feast for registry, entities, feature views,
historical retrieval, and online materialization.  
**Why:** Reuse a standard feature-store contract and PIT join implementation.  
**Alternatives:** Custom feature registry/join layer (less dependency weight,
but duplicates difficult correctness semantics); ML platform-specific
managed service (violates cost/deployment constraints).  
**Trade-off:** Feast adds versioned API behavior and integration complexity;
pin the version and validate actual offline/online paths.

## ADR-FS-002 — PostgreSQL hosts offline, online, and registry

**Status:** Accepted  
**Decision:** Reuse the current PostgreSQL instance/schema for Feast's
PostgreSQL offline store, online store, and SQL registry.  
**Why:** No new backend container and a consistent laptop footprint.  
**Alternatives:** Parquet/DuckDB offline + Redis online (more purpose-built
backends but extra deployment and skew management).  
**Trade-off:** Postgres storage and load are bounded; online store TTL is not
automatic and must be governed operationally.

## ADR-FS-003 — Read curated Gold products, never raw ingestion

**Status:** Accepted  
**Decision:** Source selected Feast inputs from existing Gold Parquet. The
bounded catalog sync is a transport into a Feast-readable Postgres source table,
not new ingestion or a second business transformation.  
**Why:** Preserves medallion ownership and source lineage.  
**Alternatives:** Read Bronze/Silver (duplicates conformance and quality logic);
write a separate ingestion path (creates a second source of truth).  
**Trade-off:** Selected snapshots consume additional Postgres storage and must
be refreshable/reconciled.

## ADR-FS-004 — Gate registration from materialization and serving

**Status:** Accepted  
**Decision:** Register candidate FeatureViews for visibility but use the
readiness manifest to skip blocked views and reject their online requests.  
**Why:** Keeps the intended feature catalog visible without turning incomplete
Gold products into trusted model inputs.  
**Alternatives:** Do not define blocked features (loses useful contracts);
materialize all views and rely on consumer caution (unsafe).  
**Trade-off:** Readiness state must be reviewed and updated alongside source
evidence; registration alone has no authorization meaning.

## ADR-FS-005 — Keep synthetic materialization isolated and labeled

**Status:** Accepted  
**Decision:** Seed a clearly labeled satellite-health demo only to exercise
registration/materialization/serving. Keep it separate from real-source rows
and restrict it to pipeline validation.  
**Why:** Proves the Feature Store works without inventing operational evidence.  
**Alternatives:** Wait for genuine mission data (leaves acceptance untested);
mix demo rows into real feature views (misleading).  
**Trade-off:** The demo is not model-ready and cannot validate domain quality.

## ADR-FS-006 — Use batch materialization on the existing scheduler

**Status:** Accepted  
**Decision:** Provide explicit incremental/backfill jobs and an hourly
Airflow DAG, triggering the same readiness-gated materialization service.  
**Why:** Current products are batch-oriented and local resources are limited;
hourly refresh supports the air-quality post-publication target without a
streaming platform.  
**Alternatives:** Streaming materialization (more state/complexity without a
demonstrated freshness requirement); manual-only operation (not repeatable).  
**Trade-off:** Upstream products remain daily and features are not streaming.
The schedule requires the feature-store profile and a configured secret token.

## ADR-FS-007 — Expose a readiness-aware local serving boundary

**Status:** Accepted  
**Decision:** Wrap Feast online retrieval with readiness, freshness, short
cache, and explicitly degraded fallback metadata. Bind host access to loopback.  
**Why:** Prevent blocked views from being consumed and make stale fallback
observable.  
**Alternatives:** Expose the generic Feast server (less code, but no per-view
release gate); add Redis (extra service).  
**Trade-off:** Process-local cache is not shared and the service is not a
general-purpose platform API.
