# Prompt 16 - API

# Enterprise Space Mission Data & AI Platform

> **Phase 16 - Platform API (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This is an **implementation** phase: build working, tested, containerized code plus docs.

---

# Objective

You are acting as Principal API Architect and Staff Backend Engineer.

Build a FastAPI service exposing data products, KPIs, model inference, and RAG queries to consumers.

---

# Critical Rules

- FastAPI + Postgres/serving layer; OpenAPI documented; containerized. Fit 16 GB RAM.
- Versioned, authenticated, rate-limited, observable; no secrets in code.
- Provide tests and one-command run.

---

# Tasks

1. API strategy: domains, consumers, contracts.
2. Endpoints: data products, KPIs, ML inference, RAG, health.
3. Schemas/contracts (pydantic), pagination, errors.
4. Auth: API keys/JWT, RBAC.
5. Versioning & deprecation.
6. Rate limiting & caching.
7. Observability: logs, metrics, tracing hooks.
8. OpenAPI + client examples.
9. Tests: unit, integration, contract.
10. ≥10 incidents (auth fail, latency, breaking change, overload, etc.).
11. Trade-offs: REST vs GraphQL · JWT vs keys · sync vs async.
12. ≥5 ADRs.

---

# Deliverables

```
api/ app/ routers/ schemas/ auth/ tests/ Dockerfile
docs/api/ 01-strategy.md ... 12-adr.md 13-glossary.md README.md
```

# Acceptance Criteria

API runs in Docker, endpoints tested, auth + versioning + OpenAPI complete, incidents documented.

# Definition of Done

A client can call data, ML, and RAG endpoints securely. Stop here.
