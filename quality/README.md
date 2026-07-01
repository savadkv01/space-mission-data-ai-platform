# Data Quality Framework — `quality/`

> **Phase 10** operational artifacts for the Space Mission Data & AI Platform.
> Narrative documentation lives in [docs/data-quality/](../docs/data-quality/);
> executable suites live in
> [transformation/quality/eo_suites.py](../transformation/quality/eo_suites.py).

Aligned to the MVP scope: six Earth-observation use cases (UC-14 change, UC-15
wildfire, UC-16 flood, UC-18 illegal fishing, UC-25 catalog, UC-27 damage) over
the Bronze → Silver → Gold medallion.

## Contents

| Area | Files |
|------|-------|
| **Rules** | [rules/earth-observation-quality-rules.md](rules/earth-observation-quality-rules.md) (MVP), [rules/satellite-quality-rules.md](rules/satellite-quality-rules.md), [rules/orbit-quality-rules.md](rules/orbit-quality-rules.md), [rules/launch-quality-rules.md](rules/launch-quality-rules.md), [rules/weather-quality-rules.md](rules/weather-quality-rules.md) (Sim) |
| **Profiling** | [profiling/profiling-strategy.md](profiling/profiling-strategy.md), [profiling/statistics-framework.md](profiling/statistics-framework.md) |
| **Monitoring** | [monitoring/monitoring-strategy.md](monitoring/monitoring-strategy.md), [monitoring/quality-kpis.md](monitoring/quality-kpis.md) |
| **Governance** | [governance/governance-model.md](governance/governance-model.md), [governance/ownership-matrix.md](governance/ownership-matrix.md) |
| **Incidents** | [incidents/production-incidents.md](incidents/production-incidents.md), [incidents/runbooks.md](incidents/runbooks.md) |

## Executable gates

| Layer | Implementation | Tests |
|-------|----------------|-------|
| Ingestion (record) | [ingestion/quality/validators.py](../ingestion/quality/validators.py), [ingestion/quality/quarantine.py](../ingestion/quality/quarantine.py) | [ingestion/tests/test_validators.py](../ingestion/tests/test_validators.py) |
| Silver / Gold (batch) | [transformation/cleaning/validation_framework.py](../transformation/cleaning/validation_framework.py), [transformation/quality/eo_suites.py](../transformation/quality/eo_suites.py) | [transformation/tests/test_eo_quality_suites.py](../transformation/tests/test_eo_quality_suites.py) |
| Sim-track marts | dbt tests in `transformation/dbt/models/gold/_gold.yml` | `dbt test` |

## Run

```powershell
cd transformation
make test        # includes the EO quality-suite tests (pure-Python, offline)
```
