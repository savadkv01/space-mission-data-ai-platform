# 06 Roadmap

## Executive Summary

This roadmap defines how the business scope can evolve from a focused MVP into a broader Space Mission Data & AI Platform. The sequence emphasizes business maturity first: prove decision value in Earth observation operations, then expand into reusable intelligence services, knowledge-centric workflows, and more advanced mission-support domains.

## Roadmap Principles

1. Start with use cases that have visible outcomes and accessible data.
2. Expand only after each version establishes credible business value.
3. Add higher-complexity aerospace operations use cases only when the platform has stronger analytical maturity.

## Version 1.0

| Dimension | Scope |
| --- | --- |
| Business Features | Wildfire monitoring, flood monitoring, illegal fishing detection, disaster impact prioritization |
| Technical Features | Common data foundation for event monitoring, searchable metadata catalog, standard operational reporting |
| AI Features | Event detection, prioritization, alert scoring, scene triage support |
| Expected Complexity | Moderate and realistic for an MVP on constrained hardware |

## Version 2.0

| Dimension | Scope |
| --- | --- |
| Business Features | Add drought and crop stress analytics plus broader EO change detection services |
| Technical Features | Broader dataset harmonization, reusable business-domain templates, improved cross-use-case reporting |
| AI Features | Spatiotemporal forecasting, multi-label classification, cross-event pattern discovery |
| Expected Complexity | Moderate to high due to broader data variety and evaluation needs |

## Version 3.0

| Dimension | Scope |
| --- | --- |
| Business Features | Expand into maritime vessel anomaly monitoring and climate emissions intelligence |
| Technical Features | Multi-domain data fusion, entity-centric analysis views, stronger evidence traceability |
| AI Features | Vessel behavior modeling, anomaly scoring, emissions hotspot detection, richer summarization |
| Expected Complexity | High because the platform starts serving multiple operational personas |

## Version 4.0

| Dimension | Scope |
| --- | --- |
| Business Features | Add space weather support and mission planning intelligence for selected operations use cases |
| Technical Features | Cross-domain event correlation, scenario analysis support, portfolio-level KPI management |
| AI Features | Forecast-driven prioritization, optimization support, knowledge retrieval for mission context |
| Expected Complexity | High because the platform begins handling mission-adjacent operational decisions |

## Version 5.0

| Dimension | Scope |
| --- | --- |
| Business Features | Extend into telemetry-driven operations, health scoring, and advanced mission support |
| Technical Features | Multi-layer decision-support environment, broader governance model, mission history intelligence |
| AI Features | Time-series anomaly detection, predictive maintenance support, RAG-enhanced operational copilots |
| Expected Complexity | Very high due to proprietary data needs, operational sensitivity, and validation demands |

## Roadmap Trade-Offs

| Option | Why It Was Not Chosen as the Starting Point |
| --- | --- |
| Start directly with spacecraft telemetry | High prestige but low feasibility with public data |
| Start with launch analytics | Sparse data and weak repeatability for a strong portfolio demo |
| Start with satcom optimization | Valuable but harder to demonstrate credibly without proprietary service data |

## Key Recommendation

Roadmap progress should be judged by business expansion, stakeholder adoption, and evidence quality rather than by the number of algorithms or tools added. The long-term platform should grow from a reliable EO intelligence base into a broader mission-support decision platform.

## Cross References

- The MVP baseline is defined in [05-mvp-definition.md](./05-mvp-definition.md).
- Ranked use cases are listed in [04-use-case-ranking.md](./04-use-case-ranking.md).
