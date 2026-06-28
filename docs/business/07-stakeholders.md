# 07 Stakeholders

## Executive Summary

The platform serves a mixed stakeholder environment where mission-oriented, commercial, and public-sector users depend on the same underlying data for different decisions. Clear stakeholder mapping is necessary to avoid designing a technically interesting platform that does not solve a real operating problem.

## Stakeholder Map

| Stakeholder Group | Primary Objectives | Main Pain Points | Decisions Supported | Priority Level |
| --- | --- | --- | --- | --- |
| Mission Control | Maintain mission continuity and respond to abnormal events | Alert fatigue, fragmented views, delayed context | Incident escalation, task prioritization, mission response | High |
| Satellite Operations | Preserve asset health and service availability | Poor early warning, inconsistent status reporting | Maintenance timing, service response, asset prioritization | High |
| Ground Operations | Maximize contact and infrastructure reliability | Conflicting schedules, equipment outages | Station allocation, repair prioritization | Medium |
| Flight Dynamics and SSA Teams | Preserve safe orbital operations | High conjunction volume, uncertain data | Risk triage, maneuver review, monitoring focus | Medium |
| EO Analysts | Detect and investigate meaningful geospatial events quickly | Manual review burden, weak metadata discoverability | Alert validation, scene prioritization, impact review | High |
| Emergency Management Agencies | Protect lives and infrastructure during disasters | Delayed impact intelligence, inconsistent coverage | Resource allocation, response prioritization, public communication | High |
| Maritime Intelligence Analysts | Detect suspicious vessel activity | Large monitoring area, spoofed identity signals | Investigation prioritization, enforcement targeting | High |
| Agriculture and Climate Analysts | Monitor environmental trends and risks | Seasonal variability, sparse validation data | Intervention targeting, reporting, risk assessment | Medium |
| Customer Success and Commercial Teams | Protect service satisfaction and renewals | Reactive visibility into customer issues | Escalation, retention action, SLA reporting | Medium |
| Scientists and Researchers | Derive trustworthy analytic insight from mission data | Data access friction, inconsistent metadata, reproducibility issues | Study prioritization, dataset selection, findings validation | Medium |
| Executive Management | Fund the right portfolio and show business results | Fragmented KPI visibility, unclear trade-offs | Investment prioritization, scope control, performance review | High |
| Regulators and Government Agencies | Ensure compliance, accountability, and public benefit | Weak traceability, delayed reporting, variable evidence quality | Oversight, enforcement, compliance review | High |

## Stakeholder Prioritization for MVP

| Tier | Stakeholders | Why They Matter First |
| --- | --- | --- |
| Tier 1 | EO analysts, emergency agencies, maritime analysts, executive management | They align directly with the recommended MVP and offer visible business outcomes |
| Tier 2 | Data stewards, scientists, regulators | They strengthen trust, discoverability, and governance |
| Tier 3 | Mission control, satellite operations, customer operations | Important for later expansion, but less feasible for the first public-data release |

## Stakeholder Tensions

1. Analysts want flexible exploration, while executives want standard KPIs and predictable reporting.
2. Public agencies want explainability and traceability, while technical teams may push for more complex models.
3. Commercial stakeholders prioritize speed and service quality, while scientific users emphasize rigor and uncertainty handling.

## Recommendation

The MVP should optimize for stakeholders who can benefit from high-frequency Earth observation insights with clear operational decisions and measurable public or commercial outcomes. That keeps scope disciplined while preserving a realistic path to future mission-operations users.

## Cross References

- KPI alignment is documented in [08-kpis.md](./08-kpis.md).
- Risk exposure by stakeholder class is documented in [09-risks.md](./09-risks.md).
