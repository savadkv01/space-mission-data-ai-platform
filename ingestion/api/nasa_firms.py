"""NASA FIRMS active-fire connector (also covers VIIRS).

Verified accessible in the pre-flight tool. Requires ``FIRMS_MAP_KEY``.
Docs: https://firms.modaps.eosdis.nasa.gov/api/area/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.base import ApiConnector, parse_csv
from ingestion.config.settings import settings


class FirmsConnector(ApiConnector):
    source_code = "FIRMS"
    rate_limit_per_s = 2

    BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    #: FIRMS area API accepts DAY_RANGE 1..5 per request.
    MAX_DAY_RANGE = 5

    def __init__(self, http=None, map_key: str | None = None) -> None:
        super().__init__(http)
        self.map_key = map_key or settings.credentials.firms_map_key

    def fetch_raw(self, *, source: str = "VIIRS_NOAA20_NRT", area: str = "-10,-10,10,10",
                  days: int = 1, date: str | None = None, max_records: int | None = None,
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        """``date`` (YYYY-MM-DD) returns ``date .. date + days - 1`` for backfill.

        ``max_records`` keeps the most recent detections and records the
        truncation in ``coverage_notes`` so capped coverage is never silent.
        """
        if not self.map_key:
            raise RuntimeError("FIRMS_MAP_KEY is not configured")
        if not 1 <= days <= self.MAX_DAY_RANGE:
            raise ValueError(f"FIRMS days must be 1..{self.MAX_DAY_RANGE}, got {days}")
        url = f"{self.BASE}/{self.map_key}/{source}/{area}/{days}"
        if date:
            url += f"/{date}"
        resp = self.http.get(url)
        resp.raise_for_status()
        text = resp.text
        if not text.lstrip("\ufeff").lower().startswith("latitude"):
            # Only a header-bearing CSV is a genuine "zero detections" answer.
            # Error/plain-text bodies (e.g. an invalid MAP_KEY) are unknown state,
            # never a current negative, so they must fail the source unit.
            raise RuntimeError(
                f"FIRMS returned a non-CSV response for area={area}: {text.strip()[:120]!r}"
            )
        records = parse_csv(text)
        if not records:
            self.log.warning("FIRMS returned zero detections for area=%s days=%s; "
                             "this does not advance observation freshness", area, days)
        if max_records is not None and len(records) > max_records:
            records.sort(key=lambda r: (r.get("acq_date", ""), str(r.get("acq_time", "")).zfill(4)),
                         reverse=True)
            note = (f"FIRMS area={area} date={date or 'latest'} days={days}: kept "
                    f"{max_records} most recent of {len(records)} detections")
            self.coverage_notes.append(note)
            self.log.warning(note)
            records = records[:max_records]
        return records, "csv"

    def _event_ts(self, record: dict[str, Any]) -> str | None:
        date = record.get("acq_date")
        time = str(record.get("acq_time", "")).zfill(4)
        if date:
            return f"{date}T{time[:2]}:{time[2:]}:00Z"
        return None
