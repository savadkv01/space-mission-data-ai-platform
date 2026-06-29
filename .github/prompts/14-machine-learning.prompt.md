# Prompt 14 - Machine Learning

# Enterprise Space Mission Data & AI Platform

> **Phase 14 - Machine Learning (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This is an **implementation** phase: build working, tested, containerized code plus docs.

---

# Objective

You are acting as Principal AI Architect, Staff ML Engineer, and MLOps Engineer.

Build end-to-end ML pipelines consuming the Phase 13 feature store: training, evaluation, registry, and inference for prioritized space use cases.

---

# Critical Rules

- Open-source only: scikit-learn / PyTorch, MLflow (tracking + registry), Feast features, Postgres/MinIO. Fit 16 GB RAM.
- Separate training and inference pipelines; both reproducible from config.
- Mandatory: data requirements first, evaluation metrics, monitoring, drift detection.
- Provide tests, seeds, and one-command training + serving.

---

# Tasks

1. ML strategy & use-case selection from the MVP scope: wildfire detection/progression, flood impact, illegal-fishing/vessel anomaly, disaster damage prioritization, EO change detection.
2. Data requirements: features from store, labels, splits, leakage prevention.
3. Training pipeline: config-driven, reproducible, MLflow runs/params/artifacts.
4. Model evaluation: metrics, baselines, validation, acceptance gates.
5. Model registry: versioning, stages, promotion criteria.
6. Inference pipeline: batch + online, feature fetch, latency SLAs.
7. Monitoring: performance, data/feature/concept drift, retrain triggers.
8. Experiment tracking & reproducibility.
9. Tests: pipeline unit/integration, model contract, smoke inference.
10. ≥10 production incidents (drift, skew, stale model, latency, label leak, etc.).
11. Trade-offs: batch vs online · sklearn vs torch · scheduled vs triggered retrain.
12. ≥5 ADRs.

---

# Deliverables

```
ml/ pipelines/ training/ inference/ models/ tests/ mlflow/
docs/ml/ 01-strategy.md ... 12-adr.md 13-glossary.md README.md
```

# Acceptance Criteria

Training runs to a registered model, eval gates enforced, inference serves predictions, drift monitoring + incidents documented.

# Definition of Done

A data scientist can train, register, deploy, and monitor a model from the repo. Stop here.
