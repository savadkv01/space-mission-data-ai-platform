# Prompt 20 - Production Incidents

# Enterprise Space Mission Data & AI Platform

> **Phase 20 - Incident Response & Runbooks (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This phase produces runbooks, playbooks, and supporting scripts.

---

# Objective

You are acting as Principal SRE and Incident Commander.

Consolidate incidents from all prior phases that define incident scenarios (10-16, 17, 19, 21-22) into a unified incident-response framework with severity, escalation, and runbooks, using the shared incident template.

---

# Critical Rules

- Reuse observability (Phase 17) signals; open-source only.
- Every runbook: symptoms, root cause, resolution, prevention.

---

# Tasks

1. Incident management strategy & severity matrix.
2. Escalation paths & on-call model.
3. Runbooks per domain (ingestion, transform, BI, ML, RAG, API, infra).
4. Detection → triage → mitigation → postmortem flow.
5. Communication & status templates.
6. Automation scripts for common recoveries.
7. SLO/error-budget policy.
8. Postmortem template & blameless culture.
9. ≥15 cross-platform incident playbooks.
10. Trade-offs: auto vs manual recovery.
11. ≥5 ADRs.

---

# Deliverables

```
incidents/ runbooks/ scripts/ templates/
docs/incidents/ 01-strategy.md ... 11-adr.md 12-glossary.md README.md
```

# Acceptance Criteria

Severity matrix, escalation, ≥15 runbooks, postmortem template complete.

# Definition of Done

An on-call engineer can resolve any documented incident via runbooks. Stop here.
