# 10 — Production Incident Scenarios

These are tabletop scenarios, not claims that incidents occurred. MTTD/MTTR
values are response targets for a single-operator laptop deployment; real
measurements must be captured in incident records.

| ID | Phase | Severity | Symptoms | Detection | Root cause | Resolution | Prevention | MTTD | MTTR |
|---|---|---|---|---|---|---|---|---:|---:|
| FS-01 | 13 | High | Values exceed the view's freshness SLA | API freshness response and scheduled-run alert | Airflow stopped or materialization cursor failed | Restore service, inspect job output, backfill a bounded interval | Six-hour DAG health check and freshness alert | 15m | 45m |
| FS-02 | 13 | High | Offline training values differ from online lookups | PIT/online parity acceptance query | Different source snapshot or transform contract | Freeze model input, align source rows, rematerialize and rerun PIT comparison | Shared FeatureView/source schema and parity test | 30m | 2h |
| FS-03 | 13 | High | Materialization task fails or online values lag | Airflow task and container logs | PostgreSQL unavailable, invalid timestamps, or source schema drift | Fix the reported prerequisite, rerun with a bounded backfill | Health dependency, schema contracts, retry-once policy | 10m | 60m |
| FS-04 | 13 | Critical | Registry definitions cannot load after restart | `/health`, bootstrap, SQL registry errors | Registry schema/table corruption or incompatible migration | Stop materialization, restore PostgreSQL backup, validate definitions before restart | Backups, pinned Feast version, migration review | 10m | 2h |
| FS-05 | 13 | Medium | Fire risk values omit detections or show unexplained count changes | Readiness endpoint and AOI reconciliation | WP1 matched/unmatched gap or accidental bypass of gate | Re-block wildfire view; retain source rows and reconcile all detections | Readiness gate integration test and review | 15m | 1h |
| FS-06 | 13 | High | Flood/vegetation feature lookups are empty or misleading | Feature readiness endpoint and zero-row profile | `silver_index` is empty or source access remains denied | Keep the view blocked; resolve approved source access and validate provenance | No synthetic substitute; source preflight and data-aware gate | 10m | 30m |
| FS-07 | 13 | High | Air-quality feature values have inconsistent magnitude | Unit profile by pollutant and serving source | O3 native units were mixed or conversion metadata lost | Block the view, restore raw value/unit evidence, correct and retest conversion | Unit-aware schemas and conversion boundary tests | 30m | 2h |
| FS-08 | 13 | Medium | Dust transport features appear with no wind observations | Null profile by feature and AOI/date | Null wind values were treated as zero or joined incorrectly | Remove transport interpretation and block wind-supported feature view | Separate AOD-only and transport contracts | 15m | 1h |
| FS-09 | 13 | High | Vessel “suspicious” score is interpreted as confirmed behavior | Consumer review / catalog caveat | One-transmission grain and heuristic flags were not surfaced | Disable the view, correct consumer language, inspect event payloads | WP5 gate and `screening_flag` naming | 30m | 2h |
| FS-10 | 13 | Medium | Online Postgres tables grow or query latency degrades | Database size and endpoint p95 | Unbounded history/backfills or excessive feature count | Pause scheduled jobs, bound retention/backfill, vacuum and capacity-test | Resource budget, query/size monitoring, batch limits | 30m | 4h |
| FS-11 | 13 | High | Cached values are returned after database recovery or outage | `cache` and `degraded` response fields | Stale fallback misunderstood as a fresh read | Verify Postgres, expire/reload cache, communicate degraded interval | Test fallback flags and keep stale window bounded | 10m | 30m |
| FS-12 | 13 | Medium | New feature version breaks an existing consumer | Contract/integration test or consumer failure | In-place semantic, unit, or entity-key change | Restore prior version and publish additive successor | Versioned names, deprecation window, consumer inventory | 30m | 2h |

For each real incident, record actual detection/resolution timestamps and
calculate measured MTTD/MTTR; do not copy the target values above as observed
performance.
