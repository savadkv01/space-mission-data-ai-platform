"""Run the data-source pre-flight using the platform's shared credentials file.

``preflight.py`` loads its own local ``.env`` (per-tool secrets), but this
repo's real API keys live in ``infrastructure/env/.env`` (used by Docker
Compose + the ingestion runner). This wrapper loads that shared file first
(``override=False`` in ``load_environment()`` means it won't be clobbered),
so a single command verifies every source with the credentials actually used
by a live full run.

Run:
    python preflight_infra_env.py             # all checks
    python preflight_infra_env.py --only firms openaq
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

import preflight

INFRA_ENV = Path(__file__).resolve().parents[2] / "infrastructure" / "env" / ".env"


if __name__ == "__main__":
    load_dotenv(INFRA_ENV)
    raise SystemExit(preflight.main())
