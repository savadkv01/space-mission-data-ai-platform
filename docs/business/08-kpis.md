# 08 KPIs

## Executive Summary

This KPI framework defines how leadership and operational stakeholders should measure the success of the Space Mission Data & AI Platform. The metrics focus on decision quality, timeliness, operational efficiency, business impact, and trust in analytics.

## KPI Principles

1. KPIs should measure business outcomes, not only technical activity.
2. The same KPI language should support analysts, operators, and executives.
3. Every MVP use case should map to a small, defensible metric set.

## KPI Catalog

| KPI | Definition | Primary Use Cases | Business Purpose |
| --- | --- | --- | --- |
| Mission Success Rate | Share of missions or mission activities completed without critical disruption | UC-01 to UC-13, UC-21 to UC-23, UC-30 | Measures reliability and continuity |
| Satellite Availability | Percentage of time the asset is operational and serviceable | UC-01 to UC-04, UC-13, UC-23 | Measures asset uptime |
| Mean Time to Detect | Average time from event occurrence to detection | UC-01, UC-03, UC-14 to UC-21, UC-27, UC-28 | Measures monitoring responsiveness |
| Mean Time to Recovery | Average time to restore normal operations after an incident | UC-01 to UC-06, UC-21, UC-29 | Measures resilience |
| Prediction Accuracy | Accuracy of forecasts, classifications, or alerts | Most AI-driven use cases | Measures AI decision quality |
| False Positive Rate | Share of generated alerts that do not correspond to meaningful events | UC-01, UC-03, UC-14 to UC-21, UC-27, UC-28 | Measures alert trustworthiness |
| False Negative Rate | Share of meaningful events missed by analytics | UC-03, UC-08, UC-14 to UC-18, UC-21, UC-27, UC-28 | Measures risk of missed action |
| Data Freshness | Time lag between data generation and availability for use | All use cases | Measures timeliness of insight |
| Alert Latency | Time from data arrival to decision-ready alert | UC-15, UC-16, UC-18, UC-21, UC-27, UC-28 | Measures operational response readiness |
| Analyst Throughput | Number of scenes, cases, or alerts handled per analyst | UC-14 to UC-19, UC-25, UC-27, UC-28 | Measures productivity |
| Search Success Rate | Percentage of analyst searches that return relevant data quickly | UC-25 and all data-discovery workflows | Measures metadata and catalog effectiveness |
| Triage Coverage | Share of high-priority events reviewed within target time | UC-08, UC-15, UC-16, UC-18, UC-27 | Measures prioritization effectiveness |
| Communication Uptime | Availability of service or customer communications | UC-06, UC-26 | Measures service continuity |
| SLA Breach Rate | Percentage of contractual commitments missed | UC-06, UC-26 | Measures commercial service quality |
| Fuel Consumption | Propellant used relative to mission objectives | UC-11 | Measures mission efficiency |
| Contact Window Utilization | Percentage of available ground-contact capacity used effectively | UC-05 | Measures resource efficiency |
| Replanning Frequency | Number of schedule or mission plan changes in a period | UC-05, UC-07, UC-09, UC-12 | Measures plan stability |
| Impact Assessment Turnaround | Time to generate a preliminary damage or impact estimate | UC-16, UC-27 | Measures disaster-response speed |
| Detection Lead Time | Advance warning before an event worsens or becomes visible through manual reporting | UC-15, UC-17, UC-20, UC-21 | Measures prevention value |
| Monitored Coverage | Share of geographic, mission, or asset scope actively monitored | UC-14 to UC-19, UC-21, UC-22, UC-28 | Measures operational reach |
| Mission Cost Variance | Difference between planned and actual mission-related cost | UC-04, UC-09, UC-11, UC-29, UC-30 | Measures financial discipline |
| Return on Mission Investment | Benefit generated relative to mission or platform spending | UC-30 and executive portfolio use cases | Measures strategic value |

## MVP KPI Set

| MVP Use Case | Core KPIs |
| --- | --- |
| Wildfire monitoring | Mean time to detect, alert latency, false negative rate, monitored coverage |
| Flood monitoring | Impact assessment turnaround, inundation accuracy, response prioritization speed |
| Illegal fishing detection | Suspicious vessel detection rate, triage coverage, response cycle time |
| Disaster damage prioritization | Time to preliminary damage estimate, asset identification accuracy, analyst throughput |
| EO change detection | Detection latency, precision, recall, area processed per analyst |
| Metadata quality and catalog management | Metadata completeness, search success rate, analyst retrieval time |

## KPI Ownership

| KPI Family | Primary Owner | Secondary Stakeholders |
| --- | --- | --- |
| Operational response metrics | Operations or agency leads | Analysts, executives |
| AI quality metrics | Analytics and AI teams | Product owners, governance teams |
| Data quality metrics | Data stewards | Analysts, platform leadership |
| Commercial metrics | Commercial and customer teams | Executives, operations |
| Financial metrics | Finance and program leadership | Executives, portfolio managers |

## Recommendation

The MVP should emphasize a compact KPI set that proves speed, quality, and decision usefulness. Too many metrics at this stage would reduce clarity and make the business value harder to communicate.

## Cross References

- Stakeholder ownership is documented in [07-stakeholders.md](./07-stakeholders.md).
- Use-case-specific KPI needs are documented in [03-use-case-analysis.md](./03-use-case-analysis.md).
