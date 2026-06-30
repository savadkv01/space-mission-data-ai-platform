"""Lightweight schema registry and validation (Task 8).

A heavy schema registry is unnecessary on a 16 GB laptop. Instead we keep
declarative field specs in code and validate at ingestion. Schemas are additive:
unknown fields are allowed (schema-on-read) but declared required fields and
type/range constraints are enforced before a record is promoted past Bronze.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class FieldSpec:
    name: str
    required: bool = True
    types: tuple[type, ...] = (object,)
    validator: Callable[[Any], bool] | None = None
    description: str = ""

    def check(self, value: Any) -> str | None:
        if value is None:
            return None if not self.required else f"{self.name}: required value is null"
        if self.types and not isinstance(value, self.types):
            return f"{self.name}: expected {[t.__name__ for t in self.types]}, got {type(value).__name__}"
        if self.validator and not self.validator(value):
            return f"{self.name}: failed constraint"
        return None


@dataclass
class Schema:
    name: str
    version: int
    fields: list[FieldSpec] = field(default_factory=list)

    @property
    def required_fields(self) -> list[str]:
        return [f.name for f in self.fields if f.required]

    def validate(self, record: dict[str, Any]) -> list[str]:
        """Return a list of human-readable errors (empty == valid)."""
        errors: list[str] = []
        for spec in self.fields:
            if spec.required and spec.name not in record:
                errors.append(f"{spec.name}: missing required field")
                continue
            err = spec.check(record.get(spec.name))
            if err:
                errors.append(err)
        return errors


def _in_range(lo: float, hi: float) -> Callable[[Any], bool]:
    return lambda v: isinstance(v, (int, float)) and lo <= float(v) <= hi


# --- Declared MVP / telemetry schemas --------------------------------------

SATELLITE_TELEMETRY = Schema(
    name="satellite_telemetry",
    version=1,
    fields=[
        FieldSpec("timestamp", types=(str,), description="ISO-8601 event time"),
        FieldSpec("satellite_id", types=(str,)),
        FieldSpec("sensor_type", types=(str,)),
        FieldSpec("payload", types=(dict,)),
        FieldSpec("metadata", required=False, types=(dict,)),
    ],
)

ORBIT_POSITION = Schema(
    name="orbit_position",
    version=1,
    fields=[
        FieldSpec("timestamp", types=(str,)),
        FieldSpec("satellite_id", types=(str,)),
        FieldSpec("latitude", types=(int, float), validator=_in_range(-90, 90)),
        FieldSpec("longitude", types=(int, float), validator=_in_range(-180, 180)),
        FieldSpec("altitude_km", types=(int, float), validator=_in_range(0, 50000)),
    ],
)

FIRMS_FIRE = Schema(
    name="firms_fire",
    version=1,
    fields=[
        FieldSpec("latitude", types=(int, float), validator=_in_range(-90, 90)),
        FieldSpec("longitude", types=(int, float), validator=_in_range(-180, 180)),
        FieldSpec("acq_date", types=(str,)),
        FieldSpec("confidence", required=False),
        FieldSpec("frp", required=False, types=(int, float)),
    ],
)

REGISTRY: dict[str, Schema] = {
    s.name: s for s in (SATELLITE_TELEMETRY, ORBIT_POSITION, FIRMS_FIRE)
}


def get_schema(name: str) -> Schema | None:
    return REGISTRY.get(name)
