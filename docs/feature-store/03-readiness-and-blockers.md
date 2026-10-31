# 03 — Readiness and Blocker Log

## Gate

The readiness manifest maps each Feast view to the source-analysis work package,
known limitation, and allowed use. `blocked` views are rejected by the online
endpoint and skipped by materialization. A registered view is only a contract;
it does not certify its source.

| Status | Materialize? | Serve? | Meaning |
|---|---|---|---|
| `blocked` | No | No; HTTP 409 with work package and blocker | Required source/quality evidence is missing. |
| `demo_only` | Only when demo seeding is explicitly enabled | Yes, labeled `synthetic_demo` and limited to pipeline validation | Demonstrates Feast behavior without operational inference. |
| `restricted` | Only when explicitly enabled | Yes, with use and freshness caveats in response | Narrow, descriptive use; not a certified analytical or decision feature. |

## Readiness-plan work tracker

| Work package | Feature-store impact | Status at Phase 13 | Evidence required to unblock |
|---|---|---|---|
| WP0 — live-versus-designed inventory | Mission, orbit, launch, weather provenance and refreshability | Open; candidate views remain blocked | Repeatable source-family reconciliation and live-state snapshot |
| WP1 — fire/AOI evidence | `wildfire_aoi_daily` | Open; blocked | Explain 98 detections vs 45 AOI-level rows; account for matched and unmatched records; brightness source/mapping conclusion |
| WP2 — spectral-index access | `spectral_index_daily` and flood/vegetation consumers | Open; blocked | Permitted source access or documented alternative, non-empty validated index rows and provenance |
| WP3 — air-quality integrity | `air_quality_aoi_daily` | Open; blocked | Native/canonical units, O3 conversion tests, null rates and coverage by measure |
| WP4 — dust context | `dust_aoi_daily` | Open; blocked | Evidence-backed time/space wind join and match-rate tests; otherwise retain AOD-only scope |
| WP5 — vessel event grain | `vessel_activity_daily` | Open; blocked | Transmission-level evidence and documented screening-flag semantics |
| WP6 — analysis-ready contracts | All production consumers | Partial in this phase; not a certification | Reviewed grain, lineage, time/spatial coverage, missingness, quality status, limitations, and representative query |

## Materialized scope

- **Synthetic satellite-health fixture:** demo-only rows used to test
  registration, materialization, online lookup, and PIT joins. Never label as
  real spacecraft health.
- **Scene catalog metadata:** 40 catalog rows can support scene discovery.
  Current event dates are stale relative to the 744-hour feature SLA. API
  responses report `stale`; refresh and WP0/WP2 evidence are needed before
  promoting the view.
- **All remaining views:** remain registered but empty, blocked, and unavailable
  to consumers.

No value is inferred to close an upstream blocker. The source-analysis plan
remains the tracking authority; this table records downstream effects and
verification criteria. A feature becomes `analysis-ready` only after the
readiness contract and domain-owner review are satisfied.
