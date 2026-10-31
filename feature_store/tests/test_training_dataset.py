from datetime import datetime, timedelta, timezone

import pandas as pd

from feature_store.training.dataset import build_training_dataset


class _RetrievalJob:
    def __init__(self, dataframe):
        self._dataframe = dataframe

    def to_df(self):
        return self._dataframe


class _FeatureStoreStub:
    def get_historical_features(self, *, entity_df, features):
        assert features == ["satellite_health_daily:health_score"]
        result = entity_df.copy()
        result["satellite_health_daily__health_score"] = 0.75
        return _RetrievalJob(result)


def test_training_dataset_version_and_entity_split_are_reproducible(tmp_path):
    base = datetime(2026, 10, 1, tzinfo=timezone.utc)
    rows = [
        {
            "sat_key": f"SAT-{index:02d}",
            "event_timestamp": base + timedelta(days=index),
            "label": index % 2,
        }
        for index in range(40)
    ]
    entity_frame = pd.DataFrame(rows)

    first = build_training_dataset(
        _FeatureStoreStub(),
        entity_dataframe=entity_frame,
        feature_refs=["satellite_health_daily:health_score"],
        entity_key="sat_key",
        label_column="label",
        split_seed="release-1",
        train_fraction=0.5,
    )
    second = build_training_dataset(
        _FeatureStoreStub(),
        entity_dataframe=entity_frame,
        feature_refs=["satellite_health_daily:health_score"],
        entity_key="sat_key",
        label_column="label",
        split_seed="release-1",
        train_fraction=0.5,
    )

    assert first.dataset_version == second.dataset_version
    assert first.manifest["row_count"] == 40
    assert set(first.train["sat_key"]).isdisjoint(set(first.validation["sat_key"]))
    assert len(first.train) + len(first.validation) == 40
    persisted = first.persist(tmp_path)
    assert (persisted / "train.parquet").is_file()
    assert (persisted / "validation.parquet").is_file()
    assert (persisted / "manifest.json").is_file()
