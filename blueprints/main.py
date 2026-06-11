"""Main blueprint for Shadow Hockey League.

Contains the leaderboard page (/) and rating redirect (/rating).
"""

from __future__ import annotations

import time

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user
from werkzeug.wrappers import Response

from models import AchievementType, Season, db
from services.cache_service import cache
from services.rating_service import build_leaderboard

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


def _is_authenticated() -> bool:
    """Return True when an admin is logged in (skip cache for them).

    The leaderboard template branches on ``current_user.is_authenticated`` to
    render the desktop-nav admin links (TIK-64). Caching the rendered HTML by
    season alone would let the first visitor's auth state leak into every
    subsequent visitor's response. Anon traffic still hits the shared
    ``leaderboard[:season]`` cache; admin requests skip it entirely so they
    always see fresh, login-aware markup.
    """
    return bool(current_user.is_authenticated)


@main.route("/")
# Flask-Caching accepts a callable for ``key_prefix`` (resolved per-request) but
# its bundled type stubs declare ``str``-only; we trust the runtime contract here.
@cache.cached(
    timeout=300,  # 5 min
    key_prefix=_leaderboard_cache_key,  # type: ignore[arg-type]
    unless=_is_authenticated,
)
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

        # Populate the season dropdown from the DB instead of hard-coding
        # it in the template. The template previously listed only 23/24,
        # 24/25, 25/26 — every other season silently disappeared from the
        # selector even though build_leaderboard happily filtered to it.
        # Newest season first matches the prod sort order.
        seasons = db.session.query(Season).order_by(Season.code.desc()).all()

        # Tooltip data (T5/TIK-61): expose multipliers and base points so the
        # template can render them from the DB instead of hard-coded HTML.
        season_multipliers = {s.code: s.multiplier for s in seasons}
        achievement_types = (
            db.session.query(AchievementType)
            .filter_by(is_active=True)
            .order_by(AchievementType.base_points_l1.desc())
            .all()
        )
        current_season = next((s.code for s in seasons if s.is_active), seasons[0].code if seasons else "25/26")

        elapsed_ms = round((time.time() - start_time) * 1000)

        # Store generation time for health check
        from flask import current_app

        current_app.config["LAST_LEADERBOARD_GEN_MS"] = elapsed_ms

        return render_template(
            "index.html",
            rating_rows=leaderboard_data,
            seasons=seasons,
            selected_season_id=season_id,
            season_multipliers=season_multipliers,
            achievement_types=achievement_types,
            current_season=current_season,
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
                show_details=current_app.debug,
            ),
            500,
        )


@main.route("/rating")
def rating() -> Response:
    """Redirect old /rating URL to main page with anchor."""
    return redirect(url_for("main.index") + "#rating", code=308)
