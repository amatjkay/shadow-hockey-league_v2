"""Cache service for managing leaderboard cache invalidation.

This module provides functions to invalidate the leaderboard cache
when managers, achievements, or countries are modified.
"""

from flask_caching import Cache

# Cache instance - to be initialized in create_app
cache = Cache()


def invalidate_leaderboard_cache() -> bool:
    """Invalidate the leaderboard cache.
    
    Call this function after:
    - Creating/updating/deleting a manager
    - Creating/updating/deleting an achievement
    - Creating/updating/deleting a country
    
    Returns:
        True if cache was invalidated, False otherwise
    """
    if cache is None:
        return False
    
    try:
        cache.delete('leaderboard')
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
