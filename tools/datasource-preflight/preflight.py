"""Pre-flight runner: verifies MVP data sources are reachable and (where
credentials are supplied) authenticated, then writes small ingestion samples.

Run:
    python preflight.py            # run all checks
    python preflight.py --only firms power      # run a subset (name substring)
    python preflight.py --list                  # list available checks

Exit code is 0 unless a required source FAILs (SKIP/WARN do not fail the run).
"""

from __future__ import annotations

import argparse
import sys

from common import FAIL, PASS, SKIP, WARN, build_session, load_environment
from sources import ALL_CHECKS


def _select(checks, only):
    if not only:
        return checks
    needles = [n.lower() for n in only]
    return [c for c in checks if any(n in c.__name__.lower() for n in needles)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Space platform data source pre-flight")
    parser.add_argument("--only", nargs="*", help="run only checks whose name matches a substring")
    parser.add_argument("--list", action="store_true", help="list available checks and exit")
    args = parser.parse_args()

    if args.list:
        for check in ALL_CHECKS:
            print(check.__name__)
        return 0

    load_environment()
    session = build_session()
    checks = _select(ALL_CHECKS, args.only)

    print("=" * 78)
    print("Space Mission Data & AI Platform — Data Source Pre-flight")
    print("=" * 78)

    results = []
    for check in checks:
        result = check(session)
        results.append(result)
        print(result.line())

    counts = {status: sum(r.status == status for r in results) for status in (PASS, FAIL, WARN, SKIP)}

    print("-" * 78)
    print(
        f"Summary: {counts[PASS]} PASS  {counts[FAIL]} FAIL  "
        f"{counts[WARN]} WARN  {counts[SKIP]} SKIP  (of {len(results)})"
    )

    skipped = [r.name for r in results if r.status == SKIP]
    if skipped:
        print("Skipped (no credentials yet): " + ", ".join(skipped))
        print("Add the missing keys to .env to verify these sources.")

    print("Samples written to ./output/ (where a check produced data).")
    print("=" * 78)

    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main())
