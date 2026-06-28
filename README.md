# Space Mission Data & AI Platform

This repository documents an enterprise-style space mission data and AI platform focused on open-data feasibility, domain research, and phased solution design. The current work emphasizes documentation and research artifacts for an Earth Observation Operations Intelligence MVP.

## Current Phase

- Phase 1 business analysis is documented under docs/business/
- Phase 2 domain research and dataset ecosystem mapping is documented under docs/domain-research/

## Repository Structure

- architecture/: system and solution design artifacts
- docs/: business analysis, domain research, and reference documentation
- infrastructure/: deployment and environment configuration
- ingestion/: data ingestion pipelines and connectors
- transformation/: transformation jobs and data processing logic
- warehouse/: warehouse-oriented data assets
- lakehouse/: lakehouse storage and related assets
- feature-store/: feature engineering and feature store artifacts
- ml/: machine learning experiments and models
- llm/: LLM-related prompts, configs, and experimentation
- vector-db/: vector database assets
- api/: service APIs and interfaces
- monitoring/: monitoring and alerting assets
- dashboards/: BI and dashboard artifacts
- tests/: test suites and validation assets
- notebooks/: exploratory notebooks
- datasets/: sample and reference datasets
- scripts/: utility and automation scripts

## Key Documentation

- docs/business/: MVP definition, use-case ranking, roadmap, stakeholders, KPIs, risks, and glossary
- docs/domain-research/: ecosystem overview, 30-source dataset catalog, data flows, quality assessment, prioritization, MVP dataset selection, and expansion roadmap

## Project Intent

The platform is designed to reflect realistic aerospace and space-data engineering thinking while remaining feasible on a 16 GB RAM laptop with Docker-based tooling and open-source components.
