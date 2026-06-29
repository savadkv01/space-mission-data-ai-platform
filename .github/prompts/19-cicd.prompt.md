# Prompt 19 - CI/CD

# Enterprise Space Mission Data & AI Platform

> **Phase 19 - CI/CD (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This is an **implementation** phase: build working pipelines plus docs.

---

# Objective

You are acting as Principal DevOps Architect and Platform Engineer.

Build GitHub Actions pipelines for lint, test, build, scan, and deploy across all components.

---

# Critical Rules

- GitHub Actions; open-source only; fit 16 GB RAM.
- Reproducible builds; gated deploys; documented rollback.

---

# Tasks

1. CI/CD strategy & branching model.
2. CI: lint, test, coverage gates.
3. Build: Docker images, versioning.
4. Security scans in pipeline.
5. CD: deploy + rollback.
6. ML/RAG model deployment gates.
7. Environments & promotion.
8. Caching & runtime optimization.
9. Tests: workflow validation, smoke deploy.
10. ≥10 incidents (flaky tests, bad deploy, rollback fail, etc.).
11. Trade-offs: mono vs multi pipeline · GHA vs self-hosted.
12. ≥5 ADRs.

---

# Deliverables

```
.github/workflows/ ci.yml cd.yml
ci/ scripts/ tests/
docs/cicd/ 01-strategy.md ... 12-adr.md 13-glossary.md README.md
```

# Acceptance Criteria

Pipelines run green, gates enforced, rollback documented, incidents listed.

# Definition of Done

A push triggers test, build, scan, deploy with rollback. Stop here.
