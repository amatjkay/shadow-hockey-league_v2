"""Main blueprint for Shadow Hockey League.

Contains the leaderboard page (/) and rating redirect (/rating).
"""

from __future__ import annotations

import time
from typing import Any

from flask import Blueprint, Response, redirect, render_template, request, url_for


from models import db
from services.rating_service import build_leaderboard
from services.cache_service import cache

main = Blueprint("main", __name__)


def _leaderboard_cache_key() -> str:
    """Build a season-scoped cache key for the leaderboard view.

    Without a season query parameter we use the bare ``"leaderboard"``
    key — keeping back-compat with ``services/cache_service.py`` and
    the tests in ``tests/integration/test_cache_invalidation.py`` that
    `cache.set("leaderboard", ...)` directly.

    With ``?season=N`` we partition the cache so each season gets its
    own entry. The fixed key would otherwise serve the first request's
    response to every later request regardless of the season selector
    (Devin Review finding on PR #19).
    """
    season = request.args.get("season")
    if season and season.isdigit():
        return f"leaderboard:{season}"
    return "leaderboard"


@main.route("/")
@cache.cached(timeout=300, key_prefix=_leaderboard_cache_key)  # 5 min
def index() -> str | tuple[str, int]:
    """Render the leaderboard page.

    Returns:
        Rendered HTML template or error page
    """
    try:
        start_time = time.time()

        season_id_raw = request.args.get("season")
        season_id = int(season_id_raw) if season_id_raw and season_id_raw.isdigit() else None

        leaderboard_data = build_leaderboard(db.session, season_id=season_id)

        elapsed_ms = round((time.time() - start_time) * 1000)

        # Handle empty database case
        if len(leaderboard_data) == 0:
            pass  # Empty leaderboard renders fine
        else:
            pass  # Normal case

        # Store generation time for health check
        from flask import current_app
        current_app.config["LAST_LEADERBOARD_GEN_MS"] = elapsed_ms

        return render_template(
            "index.html",
            rating_rows=leaderboard_data,
        )

    except Exception as e:
        import traceback as tb
        from flask import current_app

        error_traceback = tb.format_exc()
        current_app.logger.error(f"Error building leaderboard: {str(e)}", exc_info=True)
        return (
            render_template(
                "error.html",
                message="Не удалось загрузить рейтинг лиги. Попробуйте обновить страницу.",
                error_code=500,
                error_type=type(e).__name__,
                traceback=error_traceback,
                show_details=True,
            ),
            500,
        )


@main.route("/rating")
def rating() -> Response:
    """Redirect old /rating URL to main page with anchor."""
    return redirect(url_for("main.index") + "#rating", code=308)
