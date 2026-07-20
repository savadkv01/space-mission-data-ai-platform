"""Compatibility shim: ``kafka-python==2.0.2`` (pinned across the platform,
see ``ingestion/requirements.txt``) vendors an old copy of ``six`` whose
``moves`` lazy-module registration is incompatible with Python 3.12's import
system (``ModuleNotFoundError: No module named 'kafka.vendor.six.moves'``).

The ingest-runner container used elsewhere in this platform runs Python 3.11
(no problem there); the Airflow image (``apache/airflow:2.9.2``) runs Python
3.12, where the streaming pipeline DAG is the first code path to actually
import ``kafka`` in-process. Pre-registering the real (already-installed)
``six.moves`` under the name ``kafka`` expects fixes it with no changes to
kafka-python itself or its pinned version elsewhere.

Import this module (for its side effect) before importing anything from
``kafka`` or ``ingestion.common.kafka_io`` / ``ingestion.streaming.*``.
"""

from __future__ import annotations

import sys


def apply() -> None:
    if "kafka.vendor.six.moves" in sys.modules:
        return
    try:
        import six
    except ImportError:  # pragma: no cover - six is a transitive dep everywhere
        return
    sys.modules["kafka.vendor.six.moves"] = six.moves


apply()
