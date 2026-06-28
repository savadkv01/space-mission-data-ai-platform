# Prompt 01 - Business Analysis

# Enterprise Space Mission Data & AI Platform

> **Phase 1 - Business Analysis**

---

# Objective

You are acting as a senior Business Analyst, Product Owner, Domain Expert, Enterprise Architect and Technical Writer.

This phase focuses **ONLY** on understanding the business domain.

Do NOT design infrastructure.

Do NOT write code.

Do NOT generate Docker files.

Do NOT generate Spark code.

Do NOT design databases.

Do NOT discuss implementation details.

Your responsibility is to identify **what business problems this platform should solve**.

---

# Project Context

We are building an enterprise-grade **Space Mission Data & AI Platform** completely using open-source technologies.

The final platform should resemble what a real aerospace organization (such as NASA, ESA, MBRSC, Space42, Bayanat or Yahsat) could build.

The platform will eventually include

* Data Engineering
* Lakehouse
* Streaming
* Data Warehouse
* Machine Learning
* RAG
* LLM
* MLOps
* APIs
* Dashboards
* Monitoring

However, **none of those should be designed yet.**

Today's goal is only to understand the business.

---

# Scope

Think like a consultant from McKinsey, Deloitte, Accenture or BCG.

Your deliverables should be suitable for presentation to executive leadership before any software development begins.

---

# Tasks

## Task 1

Provide a detailed overview of the modern space industry.

Include

* Commercial Space
* Government Agencies
* Earth Observation
* Satellite Communication
* Navigation
* Space Exploration
* Launch Providers
* Defense
* Climate Monitoring
* Agriculture
* Maritime
* Aviation

Explain

* Current market
* Future trends
* AI adoption
* Data challenges
* Operational challenges

---

## Task 2

Identify at least **30 real-world business problems** that are solved using data engineering and artificial intelligence.

Examples

* Satellite telemetry monitoring

* Satellite health monitoring

* Satellite anomaly detection

* Predictive maintenance

* Space weather prediction

* Rocket launch analytics

* Launch failure investigation

* Fuel optimization

* Orbit prediction

* Collision avoidance

* Ground station utilization

* Satellite communication optimization

* Earth observation analytics

* Forest fire monitoring

* Ocean monitoring

* Climate monitoring

* Agricultural analytics

* Illegal fishing detection

* Disaster management

* Flood prediction

* Wildfire detection

* Space debris monitoring

* CubeSat fleet management

* Mission planning

* Payload monitoring

* Astronaut health monitoring

* Image metadata management

* Data cataloging

* Mission cost optimization

* Mission scheduling

Add additional business cases beyond this list.

---

## Task 3

For every business problem provide the following information.

### Business Problem

Describe the problem.

### Current Industry Process

Explain how organizations currently solve it.

### Existing Challenges

Explain

* operational challenges
* technical challenges
* financial challenges

### Business Impact

Explain why solving the problem matters.

### Stakeholders

Identify stakeholders.

Examples

* Mission Control

* Satellite Operations

* Scientists

* Engineers

* Executive Management

* Government Agencies

* Customers

---

### KPIs

Provide measurable KPIs.

Examples

Mission Success Rate

Satellite Availability

Prediction Accuracy

Mean Time to Detect

Mean Time to Recovery

Data Freshness

Latency

Mission Cost

Fuel Consumption

Communication Uptime

---

### Data Required

Identify required datasets.

Examples

Telemetry

Images

Orbital Data

Weather

Ground Station Logs

Maintenance Logs

Launch Logs

Sensor Data

Satellite Metadata

Mission Events

---

### AI Opportunities

Explain

Classification

Regression

Forecasting

Clustering

Anomaly Detection

Computer Vision

Natural Language Processing

Generative AI

LLM

RAG

Optimization

Simulation

---

### Risks

Explain

Operational Risks

Technical Risks

Data Risks

Security Risks

Compliance Risks

---

### Expected Business Benefits

Provide measurable improvements.

---

## Task 4

Rank every use case.

Create a scoring model using

Business Value

Implementation Complexity

Data Availability

AI Potential

Portfolio Value

Interview Value

Overall Score

Provide ranking from highest to lowest.

---

## Task 5

Recommend the best business scope for this capstone project.

The recommendation should be realistic for implementation on

* 16 GB RAM laptop

* Docker Desktop

* Open-source software only

* Free datasets only

The project should demonstrate

* Data Engineering

* Data Architecture

* AI Engineering

* Machine Learning

* Streaming

* Lakehouse

* APIs

* BI

* MLOps

without requiring enterprise-scale hardware.

Explain why each selected use case was chosen.

Explain why others were excluded.

---

## Task 6

Define the Minimum Viable Product (MVP).

Describe

Business Goals

Primary Users

Primary Features

Success Criteria

Expected Deliverables

---

## Task 7

Define the long-term roadmap.

Create roadmap versions.

Version 1.0

Version 2.0

Version 3.0

Version 4.0

Version 5.0

Each version should explain

Business Features

Technical Features

AI Features

Expected Complexity

---

## Task 8

Identify possible interview questions that a technical lead, engineering manager or recruiter might ask after reviewing this phase.

Provide detailed answers.

---

# Deliverables

Generate the following files.

```
docs/business/

README.md

01-industry-overview.md

02-business-problems.md

03-use-case-analysis.md

04-use-case-ranking.md

05-mvp-definition.md

06-roadmap.md

07-stakeholders.md

08-kpis.md

09-risks.md

10-interview-questions.md

11-glossary.md

```

---

# Documentation Standards

Use professional Markdown.

Include

* Tables
* Numbered Lists
* Cross References
* Executive Summaries
* Key Findings
* Recommendations

Write as if preparing documentation for enterprise architects and senior management.

---

# Acceptance Criteria

This phase is complete only if

* No implementation details are discussed.
* No code is generated.
* At least 30 business use cases are documented.
* Every use case has KPIs.
* Every use case includes AI opportunities.
* A ranking model is produced.
* A realistic MVP is recommended.
* A five-version roadmap is created.
* All documentation is placed under `docs/business`.

---

# Definition of Done

The phase is considered complete when a software engineering team can begin architecture design **without asking additional business questions**.

After completing this phase, stop and wait for the next prompt. Do not proceed to architecture, infrastructure, or implementation until explicitly instructed.
