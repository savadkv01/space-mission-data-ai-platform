"""Structured logging setup. Plain stdlib logging keeps the footprint small and
plays well with Docker json-file logging used by the platform."""

from __future__ import annotations

import logging

from ingestion.config.settings import settings

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        _CONFIGURED = True
    return logging.getLogger(name)
