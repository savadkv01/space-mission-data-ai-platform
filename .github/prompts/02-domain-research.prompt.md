# Prompt 02 - Domain Research (Space Data Ecosystem)

# Enterprise Space Mission Data & AI Platform

> **Phase 2 - Domain Research & Data Ecosystem Mapping**

---

# Objective

You are acting as a:

* Space Systems Domain Expert
* Data Architect
* Research Analyst
* Enterprise Architect
* Data Governance Specialist

Your goal is to deeply understand the **space data ecosystem** and identify all relevant **real-world datasets, APIs, and data streams** required to build the platform.

---

# Critical Rules

* Do NOT design infrastructure
* Do NOT write code
* Do NOT build pipelines
* Do NOT define schemas in implementation detail
* Do NOT assume enterprise paid services
* Use ONLY free and open datasets
* Focus on real-world feasibility on a 16 GB laptop
* Keep scope aligned with Phase 1 selected use cases

---

# Context

We are building a Space Mission Data & AI Platform that simulates real aerospace systems used by:

* NASA
* ESA
* MBRSC
* Space42
* Bayanat
* Yahsat

The platform will eventually support:

* Satellite telemetry analytics
* Earth observation analytics
* Space weather prediction
* Orbit tracking
* Launch analytics
* AI/ML forecasting
* LLM + RAG assistant

But for this phase:

> We only study the data ecosystem.

---

# Task 1 - Space Data Ecosystem Overview

Explain the complete space data ecosystem:

Include:

* Satellite data lifecycle
* Ground station data flow
* Mission operations data flow
* Earth observation pipelines
* Space weather systems
* Orbit determination systems
* Launch data systems

Explain:

* Where data is generated
* How it is transmitted
* How it is stored
* How it is consumed

---

# Task 2 - Identify Open Data Sources

Identify at least **25 real-world open datasets or APIs**.

Group them into categories:

## 1. Satellite Data

## 2. Earth Observation

## 3. Space Weather

## 4. Orbital / Trajectory Data

## 5. Launch Data

## 6. Astronomical Data

## 7. Climate / Environmental Data

## 8. Real-time Telemetry APIs

---

For EACH dataset provide:

### Dataset Name

### Organization

Example:

* NASA
* ESA
* NOAA
* USGS
* CelesTrak
* Space-Track (if applicable open subset)

### Type of Data

* API / File / Streaming / Bulk dataset

### Purpose

What problem it solves

### Sample Fields

Example:
timestamp, latitude, longitude, velocity, temperature, etc.

### Update Frequency

Real-time / hourly / daily / static

### Historical Depth

How far back data goes

### Data Volume Consideration

Small / Medium / Large (for local laptop feasibility)

### Use Cases in This Project

Map to Phase 1 business problems

---

# Task 3 - Data Flow Understanding

Explain:

* How satellite telemetry flows from space to ground stations
* How Earth observation imagery is processed
* How orbit prediction data is computed
* How space weather data is generated
* How launch data is recorded

Include simple Mermaid diagrams.

---

# Task 4 - Data Classification Model

Classify all datasets into:

## 1. Real-time streaming data

## 2. Batch historical data

## 3. API-based on-demand data

## 4. Static reference datasets

## 5. Machine-generated simulation data

Explain why each classification matters.

---

# Task 5 - Data Quality Assessment

For each dataset category, analyze:

* Missing values risks
* Latency issues
* Inconsistency risks
* Schema variability
* Reliability concerns
* Rate limiting issues

---

# Task 6 - Data Prioritization Strategy

Rank datasets based on:

* Relevance to Phase 1 use cases
* Ease of ingestion
* Data quality
* Portfolio value
* AI/ML potential
* Real-world industry relevance

Provide:

### Tier 1 (Must-have datasets)

### Tier 2 (Nice-to-have)

### Tier 3 (Future expansion)

---

# Task 7 - MVP Dataset Selection

Define:

* Minimum dataset set required for Phase 1 implementation
* Justification for each dataset
* What will be intentionally excluded and why

Ensure feasibility on:

* 16 GB RAM laptop
* Docker-based architecture
* Open-source tools only

---

# Task 8 - Data Risks & Constraints

Identify:

* API rate limits
* Data incompleteness
* Missing real-time feeds
* Geospatial complexity
* Storage constraints
* Processing bottlenecks

---

# Task 9 - Future Expansion Roadmap

Describe how dataset ecosystem can evolve into:

* Real-time satellite telemetry platform
* AI-powered space operations system
* Digital twin of satellite fleet
* Autonomous mission analytics system

---

# Deliverables

Generate the following structure:

```text id="9kq3lz"
docs/domain-research/

01-space-data-ecosystem-overview.md
02-dataset-catalog.md
03-data-flow-analysis.md
04-data-classification.md
05-data-quality-assessment.md
06-data-prioritization.md
07-mvp-datasets.md
08-data-risks.md
09-roadmap-expansion.md
10-glossary.md
11-references.md
```

---

# Documentation Standards

* Use professional enterprise Markdown
* Include tables for dataset comparison
* Include Mermaid diagrams for flows
* Include executive summaries
* Include clear categorization
* Include assumptions explicitly

---

# Acceptance Criteria

This phase is complete only if:

* At least 25 real datasets are documented
* All datasets are categorized
* MVP dataset set is clearly defined
* At least 3 Mermaid diagrams are included
* Data flows are clearly explained
* Clear justification for dataset selection exists

---

# Definition of Done

This phase is complete when:

> A data engineering team can start designing ingestion pipelines without asking additional questions about data sources.

Stop after completing this phase. Do NOT proceed to architecture or implementation.
