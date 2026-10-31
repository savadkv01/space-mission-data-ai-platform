# 04 — Training Data API

`feature_store.training.dataset.build_training_dataset` delegates feature
selection to Feast's PostgreSQL offline store and its point-in-time join. The
caller supplies a label-bearing entity dataframe with `event_timestamp` and
the relevant join key. Feast selects only feature values available at each
entity timestamp.

```python
training = build_training_dataset(
    store,
    entity_dataframe=events,
    feature_refs=["satellite_health_daily:health_score"],
    entity_key="sat_key",
    label_column="label",
    split_seed="use-case-v1",
)
```

## Reproducibility contract

| Output | Meaning |
|---|---|
| `dataset_version` | SHA-256 over sorted PIT result rows, feature references, split seed, and split fraction |
| `manifest` | Feature refs, label field, event-time range, input hash, split seed, and row counts |
| `train` / `validation` | Entity-stable deterministic split; all rows for one entity stay in one partition |
| PIT cutoff | Entity `event_timestamp`; future feature rows are excluded by Feast |

Splitting by entity prevents the same entity from appearing in both partitions.
The split is deterministic for a fixed seed and input dataset. A caller must
select a label source with valid provenance and temporal semantics; this helper
does not create labels or certify them.

## Limitations

- No model training, label generation, or evaluation is performed in Phase 13.
- Dataset manifests are returned to the caller; durable model/data artifact
  management belongs to the MLflow/model phase.
- PostgreSQL offline storage is bounded by the local database budget. Large
  history exports should be partitioned and capacity-tested before use.
- Blocked or demo-only features must not be used to claim operational model
  readiness.
