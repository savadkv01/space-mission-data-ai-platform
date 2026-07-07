# Prompt 10b - Climate & Air-Quality Data Quality (Extension, Implementation)

# Enterprise Space Mission Data & AI Platform

> **Phase 10b - Data Quality (Climate / Dust / Air-Quality Expansion)**
>
> Read `_shared.prompt.md` first. Extends Phase 10 (`quality/`).

---

# Objective

You are acting as:

* Data Quality Engineer
* Data Governance Specialist
* Reliability Engineer for Data

Your task is to **extend the existing data-quality framework** to cover the new climate/dust/air-quality entities.

This is an **IMPLEMENTATION phase**: working rules + tests.

---

# Scope Guardrails

* Cover only the IN-scope entities from Phase 6b/9b (air quality, aerosol/dust, atmospheric columns, derived climate indicators).
* Reuse the existing `quality/` framework (`rules/`, `profiling/`, `monitoring/`, `governance/`, `incidents/`). Do NOT create a new quality engine.

---

# Task 1 - Validation Rules

Add rules for the new Silver/Gold entities:

* **Range checks** — pollutant plausibility (PM2.5, PM10, NO₂, SO₂, CO, O₃, CH₄), AOD 0–5, LST/SST physical bounds
* **Unit checks** — enforce standardized units (µg/m³, mol/m², °C, unitless)
* **Enum checks** — pollutant codes, AOI keys, quality flags
* **Grain/uniqueness** — one row per AOI-date per mart
* **Completeness** — station coverage, valid-pixel fraction thresholds

---

# Task 2 - Freshness & Availability SLAs

Define freshness SLAs per source (near-real-time OpenAQ/TROPOMI vs daily AOD), with alerting thresholds consistent with existing monitoring.

---

# Task 3 - Profiling

Add profiling for the new entities (distributions, null rates, anomaly rates) using the existing profiling approach.

---

# Task 4 - Governance & Certification

* Register new entities in the data catalog/governance docs
* Define certification criteria for the new Gold marts (so BI/serving can mark them "certified")
* Ownership + stewardship entries

---

# Task 5 - Incident Templates

Add incident records (using the `_shared.prompt.md` incident template) for likely quality failures: TROPOMI retrieval gaps, OpenAQ station dropouts, AOD cloud contamination.

---

# Task 6 - Tests

* Unit tests for each new rule, following existing `quality/tests` conventions.
* Ensure the quality suite passes.

---

# Deliverables

```text
quality/rules/climate/                 (new validation rules)
quality/profiling/climate/             (profiling configs)
quality/monitoring/                    (extend: freshness SLAs, alerts)
quality/governance/                    (extend: catalog + certification)
quality/incidents/                     (climate incident records)
quality/tests/test_climate_rules.py
docs/data-quality/climate.md
```

---

# Critical Rules

* Implementation phase: rules run, tests pass.
* Reuse the existing quality framework; no new engine.
* Do NOT design serving/API (Phase 11b/16).

---

# Acceptance Criteria

Complete only if:

* Validation, freshness, and profiling cover all new entities
* Governance/certification and incident records added
* Tests pass

---

# Definition of Done

> New climate/dust/air-quality marts are quality-gated and certifiable, ready for trusted serving and BI.

Stop after this phase. Do NOT build the serving layer.
