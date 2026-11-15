from datetime import date

from ingestion.config.settings import settings
from ingestion.scripts.regional_ingest import firms_windows


def test_firms_windows_cover_range_in_api_sized_chunks():
    windows = firms_windows(date(2026, 10, 15), date(2026, 11, 13))
    assert windows[0] == ("2026-10-15", 5)
    assert all(1 <= days <= 5 for _, days in windows)
    assert sum(days for _, days in windows) == 30


def test_every_aoi_has_one_region_and_regional_plans_use_known_aois():
    climate = settings.climate
    assert set(climate.aoi_regions) == set(climate.aois)
    for plan in climate.region_sources.values():
        for aois in plan.values():
            assert set(aois) <= set(climate.aois)


def test_india_aois_do_not_overlap_uae_gulf_envelope():
    india = [climate_box for aoi, climate_box in settings.climate.aois.items()
             if settings.climate.aoi_regions[aoi] == "INDIA"]
    uae_max_lon = max(box[2] for aoi, box in settings.climate.aois.items()
                      if settings.climate.aoi_regions[aoi] == "UAE-GULF")
    assert min(box[0] for box in india) > uae_max_lon