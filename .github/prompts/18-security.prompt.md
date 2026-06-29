# Prompt 18 - Security

# Enterprise Space Mission Data & AI Platform

> **Phase 18 - Security (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This is an **implementation** phase: build working config plus docs.

---

# Objective

You are acting as Principal Security Architect and Platform Engineer.

Harden identity, access, secrets, and data protection across the platform; align with OWASP Top 10.

---

# Critical Rules

- Open-source only; no secrets in code; fit 16 GB RAM.
- Defense in depth; least privilege; auditability.

---

# Tasks

1. Security strategy & threat model.
2. Identity & RBAC across services.
3. Secrets management (.env, vault pattern).
4. Data protection: encryption at rest/in transit, classification, masking.
5. Network segmentation & service isolation.
6. API/RAG/ML attack surface (injection, prompt injection).
7. Audit logging & compliance mapping.
8. Vulnerability scanning & dependency hygiene.
9. Tests: authz, secret scans, policy checks.
10. ≥10 incidents (key leak, unauthorized access, injection, etc.).
11. Trade-offs: vault vs env · RBAC vs ABAC.
12. ≥5 ADRs.

---

# Deliverables

```
security/ policies/ scans/ tests/
docs/security/ 01-strategy.md ... 12-adr.md 13-glossary.md README.md
```

# Acceptance Criteria

RBAC enforced, secrets externalized, scans pass, incidents documented.

# Definition of Done

The platform meets least-privilege, secrets, and OWASP baselines. Stop here.
