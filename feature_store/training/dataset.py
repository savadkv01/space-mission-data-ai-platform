from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from feast import FeatureStore


@dataclass(frozen=True)
class TrainingDataset:
    dataset_version: str
    feature_refs: tuple[str, ...]
    train: pd.DataFrame
    validation: pd.DataFrame
    manifest: dict[str, Any]

    def persist(self, output_directory: Path) -> Path:
        destination = output_directory / self.dataset_version
        destination.mkdir(parents=True, exist_ok=True)
        self.train.to_parquet(destination / "train.parquet", index=False)
        self.validation.to_parquet(destination / "validation.parquet", index=False)
        manifest_path = destination / "manifest.json"
        manifest_path.write_text(
            json.dumps(self.manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination


def _normalized_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _frame_digest(frame: pd.DataFrame, order_fields: list[str]) -> str:
    rows = frame.sort_values(order_fields).to_dict(orient="records")
    canonical = json.dumps(
        [
            {key: _normalized_value(value) for key, value in sorted(row.items())}
            for row in rows
        ],
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _split_for_entity(entity_key: Any, seed: str, train_fraction: float) -> bool:
    digest = hashlib.sha256(f"{seed}:{entity_key}".encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:8], byteorder="big") / (2**64)
    return bucket < train_fraction


def build_training_dataset(
    store: FeatureStore,
    *,
    entity_dataframe: pd.DataFrame,
    feature_refs: list[str],
    entity_key: str,
    label_column: str,
    split_seed: str = "space-platform-v1",
    train_fraction: float = 0.8,
) -> TrainingDataset:
    required = {entity_key, "event_timestamp", label_column}
    missing = required.difference(entity_dataframe.columns)
    if missing:
        raise ValueError(f"Training entity data is missing columns: {sorted(missing)}")
    if entity_dataframe.empty:
        raise ValueError("Training entity data must contain at least one row.")
    if entity_dataframe[entity_key].isna().any():
        raise ValueError(f"{entity_key} must not contain null values.")
    if entity_dataframe["event_timestamp"].isna().any():
        raise ValueError("event_timestamp must not contain null values.")
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be strictly between 0 and 1.")
    if not feature_refs:
        raise ValueError("At least one feature reference is required.")

    ordered_refs = tuple(sorted(set(feature_refs)))
    if len(ordered_refs) != len(feature_refs):
        raise ValueError("Feature references must be unique.")

    output = store.get_historical_features(
        entity_df=entity_dataframe.copy(),
        features=list(ordered_refs),
    ).to_df()
    output["_is_train"] = output[entity_key].map(
        lambda value: _split_for_entity(value, split_seed, train_fraction)
    )
    frame_hash = _frame_digest(
        output.drop(columns=["_is_train"]),
        [entity_key, "event_timestamp"],
    )
    version_material = json.dumps(
        {
            "feature_refs": ordered_refs,
            "split_seed": split_seed,
            "train_fraction": train_fraction,
            "data_hash": frame_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    dataset_version = hashlib.sha256(version_material.encode("utf-8")).hexdigest()
    train = output.loc[output["_is_train"]].drop(columns=["_is_train"]).reset_index(drop=True)
    validation = (
        output.loc[~output["_is_train"]]
        .drop(columns=["_is_train"])
        .reset_index(drop=True)
    )
    timestamps = pd.to_datetime(output["event_timestamp"], utc=True)
    manifest = {
        "dataset_version": dataset_version,
        "feature_refs": list(ordered_refs),
        "entity_key": entity_key,
        "label_column": label_column,
        "split_seed": split_seed,
        "train_fraction": train_fraction,
        "row_count": len(output),
        "train_row_count": len(train),
        "validation_row_count": len(validation),
        "event_time_min": timestamps.min().isoformat(),
        "event_time_max": timestamps.max().isoformat(),
        "data_hash": frame_hash,
    }
    return TrainingDataset(
        dataset_version=dataset_version,
        feature_refs=ordered_refs,
        train=train,
        validation=validation,
        manifest=manifest,
    )
