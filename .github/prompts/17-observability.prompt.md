# Prompt 17 - Observability

# Enterprise Space Mission Data & AI Platform

> **Phase 17 - Observability (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This is an **implementation** phase: build working, tested, containerized config plus docs.

---

# Objective

You are acting as Principal Observability Architect and SRE.

Instrument the platform (ingestion, transforms, ML, RAG, API) with metrics, logs, and traces using Prometheus, Grafana, and OpenTelemetry already in `infrastructure/`.

---

# Critical Rules

- Reuse existing Prometheus/Grafana/OTel configs; open-source only; fit 16 GB RAM.
- Cover the three pillars: metrics, logs, traces. Define SLIs/SLOs.

---

# Tasks

1. Observability strategy & SLI/SLO catalog.
2. Metrics: exporters, pipeline/API/model KPIs.
3. Logging: structured logs, correlation IDs.
4. Tracing: OTel spans across services.
5. Dashboards: Grafana per domain.
6. Alerting: rules, thresholds, routing.
7. Health & freshness checks.
8. ML/RAG observability: drift, latency, quality.
9. Tests: alert rules, dashboard provisioning.
10. ≥10 incidents (alert storm, blind spot, dashboard down, etc.).
11. Trade-offs: pull vs push · sampling · retention.
12. ≥5 ADRs.

---

# Deliverables

```
observability/ dashboards/ alerts/ otel/ tests/
docs/observability/ 01-strategy.md ... 12-adr.md 13-glossary.md README.md
```

# Acceptance Criteria

Dashboards provision, alerts fire on thresholds, traces span services, SLOs defined.

# Definition of Done

An SRE can detect, diagnose, and alert on any failure from existing tooling. Stop here.
