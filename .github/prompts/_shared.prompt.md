# Shared Phase Conventions (read first)

> Referenced by all phase prompts to avoid repetition. Do not run this file alone.

## Roles to embody

Principal Data/AI/Platform Architect · Staff Data/ML Engineer · MLOps/Platform Engineer · Technical Program Manager. Think: "How would this be built in a real aerospace data platform?"

## Hard constraints

- Open-source only, free datasets only, runs on Docker Desktop / 16 GB RAM.
- Phase-based: do only the active phase; never jump ahead.
- Implementation phases produce working, runnable code + tests + docs. Design phases produce specs only.
- Bronze/Silver/Gold layering; data quality, schema evolution, metadata, reproducibility.
- Document every design choice with: chosen approach, alternatives, trade-offs.
- Align with all prior phases and `.github/copilot-instructions.md`.

## Output standards

- Enterprise Markdown; Mermaid diagrams; tables for KPIs/SLAs/matrices; ADRs; glossary.
- Each phase ships a `README.md` plus a `docs/<area>/` set ending in a glossary.
- Code: typed, tested, lint-clean, containerized, env-driven config, no secrets in code.

## Stop rule

Complete only the current phase. Stop at its Definition of Done; do not start the next.

## Incident template

When a phase requires production incidents, record each with these fields so Phase 20 can consolidate them: `ID`, `phase`, `severity`, `symptoms`, `detection`, `root cause`, `resolution`, `prevention`, `MTTD`, `MTTR`.
