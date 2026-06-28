# Prompt 05 - Source Data Analysis

# Enterprise Space Mission Data & AI Platform

> **Phase 5 - Source Data Analysis**

---

# Objective

You are acting as:

* Data Architect
* Data Analyst
* Space Data Domain Expert
* Data Governance Specialist

Your task is to perform a **deep technical analysis of all data sources identified in Phase 2**.

This phase is about understanding **data structure, behavior, limitations, and usability**, not ingestion design.

---

# Critical Rules

* Do NOT design ingestion pipelines
* Do NOT design architecture
* Do NOT write code
* Do NOT define Kafka, Spark, Airflow usage
* Focus ONLY on data understanding
* Use only open-source and free datasets
* Must be feasible on 16GB laptop environment

---

# Context

We are building a Space Mission Data & AI Platform using datasets from:

* NASA
* ESA
* NOAA
* USGS
* CelesTrak
* Open Notify
* ESA Copernicus
* Launch Library APIs

These datasets will power:

* Satellite analytics
* Earth observation
* Space weather forecasting
* Launch tracking
* Orbit prediction
* AI/ML models
* LLM + RAG system

---

# Task 1 - Dataset Inventory Expansion

Expand the dataset list from Phase 2.

Identify at least:

* 30–50 datasets/APIs in total

Group them into:

## 1. Satellite Telemetry Data

## 2. Earth Observation Data

## 3. Space Weather Data

## 4. Orbital Mechanics Data

## 5. Launch Data

## 6. Astronomical Data

## 7. Environmental & Climate Data

## 8. Simulation Data

---

# Task 2 - Deep Dataset Profiling

For EACH dataset provide:

### Dataset Name

### Source Organization

### Data Format (API, JSON, CSV, NetCDF, etc.)

### Data Schema (high-level fields only)

### Granularity (second/minute/hour/daily/event-based)

### Update Frequency

### Historical Coverage

### Geospatial Coverage (if applicable)

### Data Volume Estimate

### API Limitations (if any)

### Reliability Score (High/Medium/Low)

---

# Task 3 - Data Structure Analysis

Analyze:

* Field-level structure
* Common schema patterns across datasets
* Time-series structure
* Geospatial structure
* Event-based structure
* Hierarchical data structures

---

# Task 4 - Data Quality Assessment

For each dataset category identify:

* Missing data patterns
* Inconsistent timestamps
* Delayed data availability
* Sensor noise issues
* Geospatial accuracy issues
* API reliability issues
* Schema inconsistencies

---

# Task 5 - Data Suitability for Use Cases

Map datasets to Phase 1 business problems:

Example mapping:

* Satellite telemetry → anomaly detection
* Space weather → prediction models
* Launch data → delay prediction
* Earth observation → classification models

---

# Task 6 - Data Transformation Complexity

For each dataset classify:

* Low complexity transformation
* Medium complexity transformation
* High complexity transformation

Based on:

* cleaning needs
* schema complexity
* joins required
* geospatial processing needs
* time-series alignment

---

# Task 7 - Data Relationships

Identify relationships between datasets:

* Satellite ↔ telemetry ↔ orbit data
* Launch ↔ satellite deployment data
* Space weather ↔ satellite anomalies
* Earth observation ↔ climate datasets

Create a conceptual **data relationship graph (Mermaid diagram)**.

---

# Task 8 - Data Freshness Strategy

Define:

* Real-time datasets
* Near real-time datasets
* Daily batch datasets
* Static datasets

Explain impact on downstream analytics.

---

# Task 9 - Data Constraints & Risks

Identify:

* API rate limits
* Missing historical data
* Geospatial inconsistencies
* Time zone issues
* Sensor calibration issues
* Licensing restrictions (if any)
* Data duplication risks

---

# Task 10 - Data Prioritization (Refined)

Re-rank datasets based on:

* AI/ML usefulness
* Engineering feasibility
* Portfolio value
* Ease of access
* Real-world industry relevance

Define:

### Tier 1 - Core datasets (must use)

### Tier 2 - Supporting datasets

### Tier 3 - Experimental datasets

---

# Task 11 - MVP Dataset Definition

Define the **minimum dataset set required** to build Phase 6 ingestion system.

Explain:

* Why each dataset is included
* What is excluded and why
* Trade-offs made

---

# Task 12 - Future Dataset Expansion

Explain how dataset ecosystem evolves into:

* Real-time satellite constellation system
* AI-driven space operations platform
* Digital twin of orbital systems
* Autonomous mission intelligence system

---

# Deliverables

Generate:

```text id="p5fix3"
docs/source-data-analysis/

01-dataset-inventory.md
02-dataset-profiling.md
03-data-structure-analysis.md
04-data-quality-assessment.md
05-use-case-mapping.md
06-transformation-complexity.md
07-data-relationships.md
08-freshness-strategy.md
09-data-risks.md
10-data-prioritization.md
11-mvp-datasets.md
12-future-expansion.md
13-glossary.md
14-references.md
```

---

# Documentation Standards

* Enterprise-grade Markdown
* Use tables for dataset comparison
* Include Mermaid diagrams for data relationships
* Be explicit about assumptions
* Be structured like an engineering report

---

# Acceptance Criteria

This phase is complete only if:

* At least 30–50 datasets are identified
* Each dataset is fully profiled
* Dataset relationships are mapped
* MVP dataset set is defined
* Data risks are documented
* Data classification is complete

---

# Definition of Done

This phase is complete when:

> A data engineering team can design ingestion pipelines without asking any additional questions about data sources or structure.

Stop after completing this phase. Do NOT proceed to ingestion or architecture design.
