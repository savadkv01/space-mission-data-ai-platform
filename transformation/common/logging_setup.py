"""Structured logging for the transformation layer (mirrors ingestion)."""

from __future__ import annotations

import logging
import sys

from transformation.config.settings import settings

_CONFIGURED = False


def _configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root = logging.getLogger("transformation")
    root.setLevel(settings.log_level.upper())
    root.handlers[:] = [handler]
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(f"transformation.{name}")
