# Mission Operations Data Products (Simulation Track / Roadmap)

> **Not in MVP.** Mission-level aggregation is a Simulation-Track / roadmap
> concept (ADR-09). No `kpi_mission` mart is implemented in Gold yet; this catalog
> documents the intended contract so the serving layer can absorb it without
> redesign. Marked `track = sim`.

---

## Mission Timeline

| Attribute | Value |
| --- | --- |
| Product | `serving_mission_timeline` (planned) |
| Purpose | Ordered mission events/phases for a mission view |
| Owner | Simulation Track |
| Consumers | Operations dashboard (demo) |
| Refresh | Daily (sim) |
| SLA | Demo-only |
| Source | `dim_mission` + event marts (planned) |
| Grain | 1 row / mission / event |
| KPIs | phase durations, milestone completion |

---

## Mission Status

| Attribute | Value |
| --- | --- |
| Product | `serving_mission_status` (planned) |
| Purpose | Current status per mission |
| Owner | Simulation Track |
| Consumers | Operations dashboard (demo) |
| Refresh | Daily (sim) |
| SLA | Demo-only |
| Source | `dim_mission`, `fact_sat_health` |
| Grain | 1 row / mission |
| KPIs | active/degraded/complete, health rollup |

---

## Mission Success Metrics

| Attribute | Value |
| --- | --- |
| Product | `kpi_mission` (planned, per data-modeling doc) |
| Purpose | Objective-completion and uptime metrics per mission |
| Owner | Simulation Track |
| Consumers | Program leadership (demo) |
| Refresh | Daily (sim) |
| SLA | Demo-only |
| Source | mission facts (planned) |
| Grain | 1 row / mission |
| KPIs | objective_completion_pct, uptime |

> **Design note.** Because public mission data realism is weak, these products
> are intentionally deferred; the MVP delivers mission-adjacent value through the
> Earth-observation products instead.
