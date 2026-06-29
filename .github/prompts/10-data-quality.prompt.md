# Prompt 10 - Data Quality Framework

# Enterprise Space Mission Data & AI Platform

> **Phase 10 - Data Quality, Validation & Governance Foundation**

---

# Objective

You are acting as:

* Principal Data Quality Architect
* Senior Data Engineer
* Data Governance Lead
* Analytics Engineering Lead
* Site Reliability Engineer (Data)

Your task is to design the complete **enterprise Data Quality Framework** for the Space Mission Data & AI Platform.

The goal is to ensure all datasets used for analytics and AI are:

* Accurate
* Complete
* Consistent
* Timely
* Reliable
* Traceable

This phase delivers working, tested validation code.

---

# Critical Rules

* This is an IMPLEMENTATION phase: build Great Expectations suites + Spark validation jobs
* Orchestrate quality gates in Airflow; wire failures to observability
* Provide tests, seeds, one-command run; open-source only; 16 GB RAM

---

# Context

The platform ingests data from:

* Satellite telemetry
* Earth observation datasets
* Space weather APIs
* Launch event APIs
* Orbital trajectory feeds
* Synthetic telemetry generators

Data flows through:

* Bronze
* Silver
* Gold

before reaching:

* BI dashboards
* AI/ML pipelines
* LLM/RAG systems

---

# Task 1 - Data Quality Strategy

Define the overall enterprise data quality strategy.

Explain:

* Why data quality matters
* Data quality lifecycle
* Validation checkpoints
* Prevention vs correction
* Continuous quality monitoring

---

# Task 2 - Data Quality Dimensions

Define quality standards for:

* Completeness
* Accuracy
* Consistency
* Timeliness
* Validity
* Uniqueness
* Integrity
* Availability

For each dimension explain:

* Definition
* Why it matters
* Example failures
* Business impact
* Success metrics

---

# Task 3 - Dataset Quality Rules

For every major dataset category define validation rules.

Categories:

* Satellite telemetry
* Orbit data
* Launch events
* Space weather
* Earth observation
* Mission logs

For each define:

* Mandatory fields
* Optional fields
* Accepted ranges
* Referential integrity
* Duplicate rules
* Timestamp rules
* Geospatial validation

---

# Task 4 - Medallion Validation Strategy

Define validation performed at each layer.

## Bronze

* File integrity
* Schema validation
* Landing verification

## Silver

* Cleaning
* Standardization
* Deduplication
* Null handling
* Timestamp normalization

## Gold

* KPI validation
* Business rule validation
* Aggregate verification

Include Mermaid flow diagrams.

---

# Task 5 - Data Profiling Strategy

Define profiling for every dataset.

Include:

* Column statistics
* Null percentages
* Cardinality
* Distribution
* Outlier detection
* Drift indicators

Explain how profiling supports downstream engineering.

---

# Task 6 - Business Rule Validation

Define business rules such as:

* Satellite must belong to one mission
* Orbit timestamps must increase chronologically
* Launch date cannot occur after mission completion
* Sensor values must stay within engineering limits
* Weather events require valid timestamps

Document each rule with rationale.

---

# Task 7 - Data Reconciliation Strategy

Design reconciliation between:

* Source APIs
* Bronze
* Silver
* Gold

Include:

* Record counts
* Checksums
* Missing records
* Duplicate detection
* Data freshness verification

---

# Task 8 - Data Quality Monitoring

Define monitoring for:

* Failed validations
* Schema changes
* Null spikes
* Duplicate spikes
* Late-arriving data
* Pipeline failures
* Freshness SLA breaches

Map conceptual metrics to Prometheus/Grafana.

---

# Task 9 - Exception Handling

Define handling for:

* Corrupt files
* Invalid telemetry
* API failures
* Missing partitions
* Schema evolution
* Partial loads

Explain:

* Retry
* Quarantine
* Alerting
* Manual review
* Recovery

---

# Task 10 - Metadata & Lineage

Define:

* Dataset ownership
* Data lineage
* Validation history
* Audit trail
* Data certification status

---

# Task 11 - Data Governance

Define governance model:

* Data Owners
* Data Stewards
* Platform Engineers
* Data Consumers

Explain responsibilities and approval workflow.

---

# Task 12 - Quality SLAs & KPIs

Define measurable KPIs such as:

* Pipeline success rate
* Freshness SLA
* Data completeness %
* Duplicate %
* Validation pass rate
* Mean Time to Detect (MTTD)
* Mean Time to Recover (MTTR)

Provide target thresholds.

---

# Task 13 - Production Incident Scenarios

Design at least 10 realistic production incidents.

Examples:

* Satellite telemetry delayed
* NASA API unavailable
* Schema unexpectedly changes
* Duplicate launch events
* Corrupted Earth observation files
* Missing partitions
* Space weather feed outage
* Time synchronization issues
* Storage corruption
* Invalid coordinate system

For each include:

* Symptoms
* Root cause
* Detection
* Resolution
* Preventive action

---

# Task 14 - Trade-off Analysis

Explain trade-offs:

* Reject vs quarantine bad records
* Strict vs relaxed validation
* Real-time vs batch validation
* Automated vs manual correction

---

# Task 15 - Architecture Decision Records (ADR)

Create at least five ADRs.

Examples:

* Why Medallion quality gates are used
* Why data profiling is mandatory
* Why quarantine zone is preferred
* Why business rule validation occurs in Silver/Gold
* Why continuous monitoring is required

---

# Deliverables

Generate:

```text
quality/

rules/
├── satellite-quality-rules.md
├── orbit-quality-rules.md
├── launch-quality-rules.md
├── weather-quality-rules.md

profiling/
├── profiling-strategy.md
├── statistics-framework.md

monitoring/
├── monitoring-strategy.md
├── quality-kpis.md

governance/
├── governance-model.md
├── ownership-matrix.md

incidents/
├── production-incidents.md
├── runbooks.md

docs/data-quality/

01-strategy.md
02-quality-dimensions.md
03-validation-rules.md
04-medallion-validation.md
05-data-profiling.md
06-business-rules.md
07-reconciliation.md
08-monitoring.md
09-exception-handling.md
10-metadata-lineage.md
11-governance.md
12-slas-kpis.md
13-production-incidents.md
14-trade-offs.md
15-adr.md
16-glossary.md
```

---

# Documentation Standards

* Enterprise-grade Markdown
* Include validation matrices
* Include Mermaid diagrams
* Include incident response workflows
* Include SLA tables
* Clearly state assumptions

---

# Acceptance Criteria

This phase is complete only if:

* Validation strategy exists for every data domain
* Bronze, Silver and Gold quality gates are defined
* Governance model is documented
* Production incidents are documented
* Monitoring strategy is complete
* KPIs and SLAs are measurable

---

# Definition of Done

This phase is complete when:

> A data engineering team can implement enterprise-grade data quality controls and operational runbooks without requiring additional design clarification.

Stop after completing this phase. Do NOT proceed to AI/ML implementation.
