# 05 — User Personas

> Phase 12 · Task 5 — User Personas

Each persona maps to a Superset RBAC role, a default dashboard, and a defined data
access scope. Access requirements are enforced by role grants + row-level security
(see [10-security.md](./10-security.md) and
[`serving/security.md`](../../serving/security.md)).

## Persona → Role → Access Matrix

| Persona | Role | Default dashboard | Datasets | RLS scope | Access requirement |
| --- | --- | --- | --- | --- | --- |
| Executive / Program Leadership | `exec` | Executive | `platform_daily`, `aoi_validation`, read-only summaries | none (aggregates only) | Read certified aggregates; no row-level PII |
| Mission Operator — EO | `ops_eo` | Earth Observation | `wildfire_daily`, `flood_daily`, `aoi_validation`, `scene_catalog` | EO event types only | Operational detail for wildfire/flood triage |
| Mission Operator — Maritime | `ops_maritime` | EO (Maritime tab) | `vessel_activity` | maritime rows only | Suspicious-vessel triage; cannot see EO/exec |
| Data Engineer | `steward` (eng) | Platform Operations | `catalog_quality`, `scene_catalog`, observability | none | Pipeline/quality operational view |
| Data Scientist | `ai` | AI/feature view | feature/offline datasets, sim marts | none | Feature freshness, training inputs |
| Platform Engineer | `steward` | Platform Operations | observability, freshness | none | Infra health, SLA, resource usage |
| Analyst (self-service) | `analyst` | SQL Lab (personal) | all certified datasets (read) | inherits dataset RLS | Explore certified data; promote via PR |
| Demo / Interview | `demo` | Sim dashboards | `sat_health`, `launch_monthly`, `weather_impact` | none | Simulation-track only, clearly labelled |

## Persona Experiences

### Executive
Wants a 30-second read: are we detecting real events, are they trustworthy, are
we meeting SLA. Sees big-number tiles + trend, no row detail, fast (cached
aggregate).

### Mission Operator (EO)
Wants to triage: which AOIs are burning/flooding, how severe, is it corroborated.
Sees the map, severity distribution, and a drill-through table to evidence.

### Mission Operator (Maritime)
Wants a work queue: which vessels are suspicious and high-priority. RLS ensures
they see only maritime rows.

### Data Engineer / Platform Engineer
Wants operational health: DAG success, freshness, failed jobs, resource usage,
catalog quality. Cross-links to Grafana/Airflow for depth.

### Data Scientist
Wants feature/training readiness: freshness and row counts of offline datasets;
sim marts for the streaming/time-series demonstrator.

### Analyst
Explores certified datasets in SQL Lab; cannot publish ad-hoc SQL to dashboards.
Promotes useful queries by PR into `bi/datasets/sql/`.

## Alignment

Personas mirror the platform stakeholders in
[../../docs/business/07-stakeholders.md](../../docs/business/07-stakeholders.md)
and the serving access model in
[../../serving/access-strategy.md](../../serving/access-strategy.md).
