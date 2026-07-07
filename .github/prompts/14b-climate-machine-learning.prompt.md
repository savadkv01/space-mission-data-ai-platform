# Prompt 14b - Machine Learning (Climate / Dust / Air-Quality Extension)

# Enterprise Space Mission Data & AI Platform

> **Phase 14b - Machine Learning (Climate Expansion, Implementation)**

Read `.github/prompts/_shared.prompt.md` first. Extends Phase 14 (`ml/`). This is an **implementation** phase: build working, tested code plus docs.

---

# Objective

You are acting as Principal AI Architect, Staff ML Engineer, and MLOps Engineer.

Build **light ML pipelines** for climate/dust/air-quality use cases, consuming the Phase 13b features, reusing the existing training/inference/MLflow stack.

---

# Scope Guardrails

- Reuse existing training + inference pipelines, MLflow tracking/registry, Feast features. No new infra. Fit 16 GB RAM.
- Build only tabular/light models plus optional lightweight CV; do NOT build heavy forecast models that depend on CAMS/ERA5 gridded data or geostationary imagery (deferred).
- Separate training and inference; reproducible from config.

---

# Tasks

1. Use-case selection (light scope):
   - **AOD → PM2.5/PM10 regression** (calibrate satellite aerosol to ground OpenAQ).
   - **Dust event forecast (6-48h)** from AOD + wind + recency features (tabular timeseries).
   - **Heatwave / LST-anomaly forecast** (tabular timeseries).
   - **Optional CV**: dust/smoke vs cloud segmentation on Sentinel-2 tiles (only if it fits 16 GB; else defer).
2. Data requirements: features from 13b, labels (OpenAQ PM ground-truth, observed dust days), splits, leakage prevention.
3. Training pipeline: config-driven, MLflow runs/params/artifacts.
4. Evaluation: regression (MAE/RMSE) + classification (precision/recall for dust events); baselines; acceptance gates.
5. Model registry: versioning, stages, promotion criteria.
6. Inference: batch (daily marts) + online (air-quality); latency SLAs.
7. Monitoring: performance + feature/concept drift; retrain triggers.
8. Tests: pipeline unit/integration, model contract, smoke inference.
9. Trade-offs + ≥3 ADRs (regression model choice, forecast horizon, defer-CV decision).

---

# Deliverables

```
ml/pipelines/climate/    training/ inference/ models/
ml/tests/test_climate_ml.py
docs/ml/climate.md
```

# Acceptance Criteria

At least the AOD→PM regression and dust-event forecast train to registered models, eval gates enforced, inference serves predictions, drift monitoring documented.

# Definition of Done

A data scientist can train, register, deploy, and monitor climate/dust/air-quality models from the repo. Stop here.
