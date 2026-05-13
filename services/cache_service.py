"""Cache service for managing leaderboard cache invalidation.

This module provides functions to invalidate the leaderboard cache
when managers, achievements, or countries are modified.
"""

from __future__ import annotations

import logging

from flask_caching import Cache
from flask_caching.backends.rediscache import RedisCache
from flask_caching.backends.simplecache import SimpleCache

# Cache instance - to be initialized in create_app
cache: Cache = Cache()

logger = logging.getLogger(__name__)

# Cache-key contract owned by ``blueprints/main.py::_leaderboard_cache_key``:
# the bare ``"leaderboard"`` key (no season selector) and one
# ``"leaderboard:{season_id}"`` variant per season query parameter.
_LEADERBOARD_PREFIX = "leaderboard"


def invalidate_leaderboard_cache() -> bool:
    """Delete only the ``leaderboard*`` entries from the cache backend.

    The leaderboard view at ``blueprints/main.py:index`` partitions its cache
    per ``?season=N`` query parameter, producing the keys ``"leaderboard"``
    and ``"leaderboard:{season_id}"``. Earlier revisions of this helper
    called ``cache.clear()``, which scrubbed every namespace in the same
    backend (rate-limiter counters, Flask-Limiter state, etc.). Now we
    target the ``leaderboard*`` prefix only and leave unrelated keys alone.

    Backend dispatch:

    - ``RedisCache``: ``SCAN`` over
      ``{CACHE_KEY_PREFIX}leaderboard*`` via ``cache.cache._write_client``
      and ``DELETE`` the matching keys in one batch. ``CACHE_KEY_PREFIX`` is
      honoured automatically because ``cachelib`` stores it on
      ``RedisCache.key_prefix``.
    - ``SimpleCache``: iterate ``cache.cache._cache`` and ``cache.delete``
      every key starting with ``"leaderboard"``.
    - Unknown backend: fall back to ``cache.clear()`` and log a warning so
      a future custom backend does not silently retain stale entries.

    Call this after:
    - Creating/updating/deleting a manager
    - Creating/updating/deleting an achievement
    - Creating/updating/deleting a country

    Returns:
        True on success, False if the backend was not initialised or the
        deletion raised.
    """
    if cache is None:
        return False

    backend = getattr(cache, "cache", None)
    if backend is None:
        return False

    try:
        if isinstance(backend, RedisCache):
            client = backend._write_client
            redis_key_prefix = getattr(backend, "key_prefix", "") or ""
            pattern = f"{redis_key_prefix}{_LEADERBOARD_PREFIX}*"
            keys = list(client.scan_iter(match=pattern))
            if keys:
                client.delete(*keys)
            return True

        if isinstance(backend, SimpleCache):
            for key in list(backend._cache.keys()):
                if key.startswith(_LEADERBOARD_PREFIX):
                    cache.delete(key)
            return True

        logger.warning(
            "invalidate_leaderboard_cache: unknown backend %s; " "falling back to cache.clear()",
            type(backend).__name__,
        )
        cache.clear()
        return True
    except Exception:
        logger.exception("invalidate_leaderboard_cache failed")
        return False


def get_cache_stats() -> dict:
    """Get cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    if cache is None:
        return {"status": "not_initialized"}

    try:
        config = cache.config or {}
        return {
            "status": "ok",
            "cache_type": config.get("CACHE_TYPE", "unknown"),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
