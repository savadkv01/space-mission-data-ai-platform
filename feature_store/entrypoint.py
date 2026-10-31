from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

from feature_store.database import configure_registry_url, initialize_source_tables


def bootstrap() -> None:
    configure_registry_url()
    initialize_source_tables()

    if os.environ.get("FEATURE_STORE_LOAD_GOLD", "false").lower() == "true":
        from feature_store.materialize.gold_sync import sync_enabled_gold_sources

        print({"gold_sync": sync_enabled_gold_sources()}, flush=True)

    if os.environ.get("FEATURE_STORE_DEMO_SEED", "false").lower() == "true":
        from feature_store.demo_seed import seed_satellite_health_demo

        print(
            {"demo_seed_rows": seed_satellite_health_demo()},
            flush=True,
        )

    repo_path = Path(
        os.environ.get(
            "FEAST_REPO_PATH",
            str(Path(__file__).parent / "feature_repo"),
        )
    )
    if str(repo_path) not in sys.path:
        sys.path.insert(0, str(repo_path))
    from entities import ENTITIES
    from feature_views import FEATURE_SERVICES, FEATURE_VIEWS
    from feast import FeatureStore

    store = FeatureStore(repo_path=str(repo_path))
    store.apply([*ENTITIES, *FEATURE_VIEWS, *FEATURE_SERVICES])

    from feature_store.materialize.runner import materialize_eligible

    report = materialize_eligible(store)
    print({"initial_materialization": [item.__dict__ for item in report]}, flush=True)


def main() -> None:
    bootstrap()
    uvicorn.run(
        "feature_store.api.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("FEATURE_STORE_CONTAINER_PORT", "6566")),
        workers=1,
        access_log=True,
    )


if __name__ == "__main__":
    main()
