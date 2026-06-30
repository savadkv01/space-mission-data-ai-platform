# Validation Framework

> Code: [validation_framework.py](validation_framework.py) · Spec: [docs/transformation/12-data-quality.md](../../docs/transformation/12-data-quality.md)

Lightweight, dependency-free expectations run as **checkpoints between layers** (a laptop-sized analogue of Great Expectations).

## Expectations

| Builder | Checks |
| --- | --- |
| `expect_row_count_min(n)` | batch not unexpectedly empty |
| `expect_not_null(field)` | field populated on every row |
| `expect_unique(keys)` | natural key unique after dedup |
| `expect_value_in_range(field, lo, hi)` | values within bounds |

## Severity

| Severity | Effect |
| --- | --- |
| `critical` | failure blocks promotion (orchestrator fails task) |
| `warn` | logged, raises metric, allows promotion |

`run_checkpoint(rows, expectations)` → `CheckpointResult(passed, failures, warnings, stats)`.

## Gold-layer counterpart

dbt tests (`not_null`, `unique`, `dbt_utils.accepted_range`, `unique_combination_of_columns`) enforce the same guarantees on Gold — see [../dbt/models/gold/_gold.yml](../dbt/models/gold/_gold.yml).
