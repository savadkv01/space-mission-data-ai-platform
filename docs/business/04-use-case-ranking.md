# 04 Use-Case Ranking

## Executive Summary

This ranking model prioritizes business use cases for the Space Mission Data & AI Platform based on business value, capstone feasibility, data access realism, AI relevance, portfolio strength, and interview value. The model favors use cases that can demonstrate strong end-to-end business outcomes on open data and a single-machine environment while retaining credible aerospace alignment.

## Scoring Model

### Criteria

| Criterion | Definition | Weight |
| --- | --- | --- |
| Business Value | Expected operational, commercial, or public-sector value if solved well | 25% |
| Implementation Complexity | Relative difficulty for a solo capstone on a 16 GB laptop, where lower complexity scores better | 15% |
| Data Availability | Practical availability of free and usable datasets | 20% |
| AI Potential | Opportunity to demonstrate meaningful AI or ML outcomes | 15% |
| Portfolio Value | Strength of the use case in showing broad platform capability | 15% |
| Interview Value | Likelihood the use case creates strong technical discussion in interviews | 10% |

### Scoring Method

1. Each criterion is scored from 1 to 5.
2. Higher is better for every criterion, including Implementation Complexity where 5 means relatively feasible and 1 means highly difficult.
3. Overall score is normalized to a 100-point scale.

Formula:

Overall Score = ((Business Value x 25) + (Implementation Complexity x 15) + (Data Availability x 20) + (AI Potential x 15) + (Portfolio Value x 15) + (Interview Value x 10)) / 5

## Ranked Portfolio

| Rank | ID | Use Case | Business Value | Implementation Complexity | Data Availability | AI Potential | Portfolio Value | Interview Value | Overall Score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | UC-15 | Wildfire detection and progression monitoring | 5 | 4 | 5 | 5 | 5 | 5 | 95 |
| 2 | UC-16 | Flood monitoring and impact assessment | 5 | 4 | 5 | 5 | 5 | 5 | 95 |
| 3 | UC-18 | Illegal fishing detection | 5 | 4 | 5 | 5 | 5 | 5 | 95 |
| 4 | UC-27 | Disaster damage assessment prioritization | 5 | 4 | 5 | 5 | 5 | 5 | 95 |
| 5 | UC-14 | Earth observation change detection | 5 | 4 | 5 | 5 | 5 | 4 | 93 |
| 6 | UC-17 | Drought and crop stress analytics | 5 | 4 | 5 | 4 | 5 | 4 | 90 |
| 7 | UC-25 | Image metadata quality and catalog management | 4 | 5 | 5 | 4 | 5 | 4 | 89 |
| 8 | UC-28 | Climate emissions and methane monitoring | 5 | 3 | 4 | 5 | 5 | 5 | 87 |
| 9 | UC-19 | Maritime vessel anomaly detection | 4 | 4 | 5 | 4 | 4 | 4 | 84 |
| 10 | UC-21 | Space weather forecasting support | 5 | 3 | 4 | 4 | 5 | 4 | 84 |
| 11 | UC-26 | Satcom customer SLA assurance | 5 | 3 | 3 | 4 | 5 | 4 | 79 |
| 12 | UC-30 | Mission cost and portfolio optimization | 5 | 3 | 3 | 4 | 5 | 4 | 79 |
| 13 | UC-20 | Aviation weather risk intelligence | 4 | 3 | 4 | 4 | 4 | 4 | 77 |
| 14 | UC-12 | Mission planning and scheduling | 5 | 2 | 3 | 4 | 5 | 4 | 77 |
| 15 | UC-06 | Satellite communication capacity optimization | 5 | 2 | 3 | 4 | 5 | 4 | 77 |
| 16 | UC-29 | Ground equipment maintenance analytics | 4 | 3 | 3 | 4 | 4 | 3 | 70 |
| 17 | UC-05 | Ground station scheduling optimization | 4 | 2 | 3 | 4 | 4 | 4 | 69 |
| 18 | UC-13 | Payload performance monitoring | 4 | 2 | 2 | 4 | 4 | 4 | 65 |
| 19 | UC-22 | Space debris monitoring and prioritization | 4 | 2 | 3 | 3 | 4 | 4 | 65 |
| 20 | UC-23 | CubeSat fleet operations management | 4 | 2 | 2 | 4 | 4 | 4 | 61 |
| 21 | UC-04 | Predictive maintenance for space assets | 4 | 2 | 2 | 4 | 4 | 3 | 59 |
| 22 | UC-07 | Orbit prediction support | 4 | 2 | 3 | 3 | 3 | 4 | 59 |
| 23 | UC-11 | Fuel optimization for station keeping | 4 | 1 | 2 | 4 | 4 | 4 | 55 |
| 24 | UC-08 | Collision avoidance prioritization | 5 | 1 | 2 | 4 | 5 | 5 | 55 |
| 25 | UC-01 | Satellite telemetry monitoring | 5 | 1 | 1 | 4 | 5 | 4 | 54 |
| 26 | UC-03 | Satellite anomaly detection | 5 | 1 | 1 | 5 | 5 | 5 | 54 |
| 27 | UC-02 | Satellite health scoring | 4 | 1 | 1 | 4 | 4 | 4 | 46 |
| 28 | UC-09 | Launch readiness analytics | 4 | 1 | 1 | 3 | 4 | 4 | 43 |
| 29 | UC-10 | Launch failure investigation support | 4 | 1 | 1 | 4 | 4 | 5 | 43 |
| 30 | UC-24 | Astronaut health and habitat monitoring | 5 | 1 | 1 | 4 | 4 | 5 | 42 |

## Key Findings

1. The top-ranked portfolio clusters around Earth observation, disaster intelligence, and maritime monitoring because these use cases have strong open-data ecosystems and visible business outcomes.
2. Several classic aerospace operations use cases remain strategically important but rank lower because free data access is weak and validation is difficult in a public capstone.
3. Metadata quality and cataloging rank highly because they enable every downstream analytic product and clearly demonstrate business thinking beyond model building.

## Recommended Shortlist for Capstone Scope

| Priority Tier | Use Cases | Rationale |
| --- | --- | --- |
| Tier 1 | UC-15, UC-16, UC-18, UC-27 | High business value, strong open data, clear alerting and decision workflows |
| Tier 2 | UC-14, UC-17, UC-25 | Extends the platform into reusable EO intelligence and data management |
| Tier 3 | UC-19, UC-21, UC-28 | Strong future expansion paths once MVP capabilities are established |

## Why Some High-Prestige Use Cases Rank Lower

| Use Case Type | Reason for Lower Rank |
| --- | --- |
| Satellite telemetry and anomaly operations | Requires proprietary telemetry, mission context, and realistic labeling |
| Launch analytics | Very limited open data and difficult validation against rare events |
| Collision avoidance and fuel optimization | Strong interview value but difficult to demonstrate safely and credibly with public data |
| Human spaceflight health monitoring | Highly sensitive data and weak public-data access |

## Recommendation

The best business scope is an Earth Observation Operations Intelligence portfolio anchored on disaster monitoring, maritime anomaly detection, and metadata quality. This scope preserves aerospace credibility while remaining realistic under the project constraints.

## Cross References

- Business rationale for the selected use cases is described in [05-mvp-definition.md](./05-mvp-definition.md).
- Detailed use-case analysis is documented in [03-use-case-analysis.md](./03-use-case-analysis.md).
- KPI alignment is documented in [08-kpis.md](./08-kpis.md).
