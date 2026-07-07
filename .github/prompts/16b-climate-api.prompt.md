# Prompt 16b - API (Climate / Dust / Air-Quality Extension)

# Enterprise Space Mission Data & AI Platform

> **Phase 16b - Platform API (Climate Expansion, Implementation)**

Read `.github/prompts/_shared.prompt.md` first. Extends Phase 16 (`api/`). This is an **implementation** phase: build working, tested code plus docs.

---

# Objective

You are acting as Principal API Architect and Staff Backend Engineer.

Extend the existing FastAPI service with **climate, dust, and air-quality endpoints** for data products, KPIs, model inference, and RAG, reusing the existing app structure.

---

# Scope Guardrails

- Reuse the existing FastAPI app, auth, versioning, rate limiting, and observability. No new frameworks. Fit 16 GB RAM.
- Endpoints map 1:1 to certified 11b products and 14b/15b models; no new business logic.
- No secrets in code; OpenAPI documented; containerized.

---

# Tasks

1. Data-product endpoints (mirror existing patterns):
   - `/air-quality/daily/{aoi_key}/{date}`
   - `/dust/events/{aoi_key}/{date}`
   - `/climate/indicators/{aoi_key}/{date}`
   - `/vegetation/health/{aoi_key}/{date}`
2. KPI endpoints: air-quality/dust/climate KPIs from the materialized aggregate.
3. ML inference endpoints: AOD→PM prediction, dust-event forecast, LST-anomaly forecast (from 14b registry).
4. RAG endpoint: environmental report / climate summary (from 15b).
5. Schemas/contracts (pydantic), pagination, errors for new endpoints.
6. Auth + RBAC + rate limiting + caching applied consistently.
7. Observability: logs/metrics/tracing hooks for new routes.
8. OpenAPI + client examples for new endpoints.
9. Tests: unit, integration, contract for new routes.
10. Trade-offs + ≥3 ADRs (endpoint grain, sync vs async inference, caching TTL).

---

# Deliverables

```
api/app/routers/climate.py    (new routers: air-quality, dust, climate, vegetation, ml, rag)
api/app/schemas/climate.py
api/tests/test_climate_api.py
docs/api/climate.md
```

# Acceptance Criteria

New endpoints run in Docker, tested, auth + versioning + OpenAPI complete, consistent with existing API conventions.

# Definition of Done

A client can securely call climate/dust/air-quality data, KPI, ML, and RAG endpoints. Stop here.

---

> After 16b, run phases 17-25 (observability, security, CI/CD, incidents, testing, performance, docs, review) once — they cover the new climate components automatically with no climate-specific prompt needed.
