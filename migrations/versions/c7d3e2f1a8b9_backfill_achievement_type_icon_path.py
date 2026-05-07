"""backfill_achievement_type_icon_path

Backfill ``achievement_types.icon_path`` for the six canonical types and
rewrite any ``achievements.icon_path`` rows that still point at a
non-existent SVG file (e.g. ``r3.svg`` written by the admin form when
``AchievementType.icon_path`` was NULL).

Background
----------
``58667e02fd0d`` added the ``icon_path`` column with a server default of
``/static/img/cups/default.svg``, but that default only fires on
``INSERT`` — existing seeded rows kept ``NULL``. ``models.py``'s
``AchievementType.get_icon_url`` then constructed a fallback path
``/static/img/cups/{code.lower()}.svg`` that resolved to filenames which
do not exist for every code (``best.svg`` / ``r3.svg`` / ``r1.svg``),
producing 404s in the public leaderboard view (:doc:`TIK-77`).

This migration:

1. UPDATEs ``achievement_types`` rows with ``icon_path IS NULL`` (or
   default-string) to the canonical filename per ``code``.
2. UPDATEs ``achievements`` rows that previously persisted a synthesised
   non-existent path (only ``r3.svg`` was observed in the wild on
   staging, but ``r1.svg`` / ``best.svg`` are rewritten as well for
   defence-in-depth — those filenames also do not exist on disk).

Both are idempotent and safe to re-run.

Revision ID: c7d3e2f1a8b9
Revises: b5f2a8e1c34d
Create Date: 2026-05-05 19:50:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7d3e2f1a8b9"
down_revision: Union[str, None] = "b5f2a8e1c34d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Canonical mapping: AchievementType.code → filename in ``static/img/cups/``.
# Mirrors the seed migrations for L1 / L2.1 / L2.2 25/26.
_CANONICAL_ICON_PATHS: dict[str, str] = {
    "TOP1": "/static/img/cups/top1.svg",
    "TOP2": "/static/img/cups/top2.svg",
    "TOP3": "/static/img/cups/top3.svg",
    "BEST": "/static/img/cups/best-reg.svg",
    "R3": "/static/img/cups/hockey-sticks-and-puck.svg",
    "R1": "/static/img/cups/hockey-sticks-and-puck.svg",
}

# Synthesised paths that ``AchievementType.get_icon_url`` could leak into
# ``achievements.icon_path`` before TIK-77. Each maps to the canonical
# real file the admin form should have written.
_BROKEN_PATH_REWRITES: dict[str, str] = {
    "/static/img/cups/r3.svg": "/static/img/cups/hockey-sticks-and-puck.svg",
    "/static/img/cups/r1.svg": "/static/img/cups/hockey-sticks-and-puck.svg",
    "/static/img/cups/best.svg": "/static/img/cups/best-reg.svg",
}


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Backfill achievement_types.icon_path
    rows = bind.execute(
        sa.text(
            "SELECT id, code, icon_path FROM achievement_types "
            "WHERE icon_path IS NULL OR icon_path = '' "
            "OR icon_path = '/static/img/cups/default.svg'"
        )
    ).fetchall()

    for row in rows:
        type_id, code, current = row
        canonical = _CANONICAL_ICON_PATHS.get((code or "").upper())
        if canonical is None:
            # Unknown code (custom AchievementType added by ops); leave
            # whatever default is there alone — don't guess.
            continue
        bind.execute(
            sa.text("UPDATE achievement_types SET icon_path = :path WHERE id = :id"),
            {"path": canonical, "id": type_id},
        )

    # 2. Rewrite previously-persisted broken paths on achievements rows.
    for broken, canonical in _BROKEN_PATH_REWRITES.items():
        bind.execute(
            sa.text("UPDATE achievements SET icon_path = :canonical " "WHERE icon_path = :broken"),
            {"canonical": canonical, "broken": broken},
        )


def downgrade() -> None:
    """Revert the backfill, but only for rows that still match what we wrote.

    Manually-curated icon paths entered after this migration ran are kept
    untouched.
    """

    bind = op.get_bind()

    for code, canonical in _CANONICAL_ICON_PATHS.items():
        bind.execute(
            sa.text(
                "UPDATE achievement_types SET icon_path = NULL "
                "WHERE code = :code AND icon_path = :path"
            ),
            {"code": code, "path": canonical},
        )

    # Best-effort: re-instate the broken paths is undesirable (they 404),
    # so the achievements rewrite is intentionally one-way.
