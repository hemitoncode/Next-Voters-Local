"""In-memory cache for city pipeline reports.

This module provides a simple module-level cache for storing and retrieving
city-specific markdown reports. The module itself acts as a singleton —
import it from anywhere to access the same cached data.

Used by the container runner to store reports as pipelines complete,
and by the email dispatcher to retrieve them for delivery.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_cache: dict[str, str] = {}


def store(city: str, report: str) -> None:
    """Store a report for a city. Skips empty/falsy reports."""
    if report:
        _cache[city] = report


def get(city: str) -> str | None:
    """Retrieve a cached report by city name."""
    return _cache.get(city)


def get_all() -> dict[str, str]:
    """Return a copy of all cached reports."""
    return dict(_cache)


def build_from_results(results: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Populate the cache from pipeline results and return all cached reports.

    Clears existing cache, then stores each city's markdown_report if non-empty.
    This replaces the former build_city_reports_dict() function.

    Args:
        results: Pipeline results indexed by city name.

    Returns:
        Copy of all cached reports as a dict.
    """
    clear()
    for city, result in results.items():
        store(city, result.get("markdown_report", ""))

    logger.info(f"Cached reports for {len(_cache)} cities")
    return get_all()


def clear() -> None:
    """Clear all cached reports."""
    _cache.clear()
