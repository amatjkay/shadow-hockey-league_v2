"""Cache service for managing leaderboard cache invalidation.

This module provides functions to invalidate the leaderboard cache
when managers, achievements, or countries are modified.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask_caching import Cache

if TYPE_CHECKING:
    from typing import Any

# Cache instance - to be initialized in create_app
cache: Cache = Cache()


def invalidate_leaderboard_cache() -> bool:
    """Invalidate the leaderboard cache (all season-scoped variants).

    The leaderboard view at ``blueprints/main.py:index`` uses a callable
    cache key that partitions per ``?season=N`` query parameter. Deleting
    the bare ``"leaderboard"`` key alone would leave stale per-season
    entries behind. We clear the whole cache, which mirrors what
    ``services/admin.py::SHLAdminIndexView.flush_cache`` already does
    and is the only reliable strategy for backends without prefix
    deletion (SimpleCache; Redis without SCAN-based delete).

    Call this after:
    - Creating/updating/deleting a manager
    - Creating/updating/deleting an achievement
    - Creating/updating/deleting a country

    Returns:
        True if cache was cleared, False otherwise.
    """
    if cache is None:
        return False

    try:
        cache.clear()
        return True
    except Exception:
        return False


def get_cache_stats() -> dict:
    """Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    if cache is None:
        return {"status": "not_initialized"}
    
    try:
        return {
            "status": "ok",
            "cache_type": cache.config.get('CACHE_TYPE', 'unknown'),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
