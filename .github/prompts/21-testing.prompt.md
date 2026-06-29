# Prompt 21 - Testing

# Enterprise Space Mission Data & AI Platform

> **Phase 21 - Testing Strategy (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This is an **implementation** phase: build tests plus docs.

---

# Objective

You are acting as Principal QA Architect and Staff Engineer.

Build the unified test suite: unit, integration, e2e, data-quality, and regression across all components.

---

# Critical Rules

- pytest + Great Expectations; open-source only; fit 16 GB RAM.
- Deterministic, isolated, CI-runnable tests.

---

# Tasks

1. Test strategy & pyramid.
2. Unit tests per module.
3. Integration tests across pipelines.
4. E2E platform tests.
5. Data-quality tests.
6. ML/RAG tests: contracts, eval, regression.
7. Performance/smoke tests.
8. Coverage targets & gates.
9. Test data & fixtures.
10. ≥10 incidents (flaky, false pass, slow suite, etc.).
11. Trade-offs: mocking vs real · coverage vs speed.
12. ≥5 ADRs.

---

# Deliverables

```
tests/ unit/ integration/ e2e/ data/ ml/
docs/testing/ 01-strategy.md ... 12-adr.md 13-glossary.md README.md
```

# Acceptance Criteria

Suite runs in CI, gates enforced, all layers covered, incidents documented.

# Definition of Done

A dev can validate the whole platform with one command. Stop here.
