"""normalize_admin_achievement_title

Rewrite ``achievements.title`` rows that were created via the admin form
with the redundant ``"{type.name} {league.name} {season.name}"`` pattern
back to just ``"{type.name}"``. The HTML tooltip wrapper in
``models.py::Achievement.to_html`` already supplies league + season, so
the duplication produced hover strings like

    Shadow 2.1 league Round 3 League 2.1 Season 2025/26 s25/26

after the admin form path stored ``title='Round 3 League 2.1 Season
2025/26'`` (:doc:`TIK-78`).

This migration only touches rows whose title is *exactly* the legacy
admin-form pattern; manually-curated titles are preserved.

Revision ID: d8e4f3a2b9c0
Revises: c7d3e2f1a8b9
Create Date: 2026-05-05 19:55:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8e4f3a2b9c0"
down_revision: Union[str, None] = "c7d3e2f1a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    rows = bind.execute(sa.text("""
            SELECT a.id AS achievement_id,
                   a.title AS achievement_title,
                   t.name AS type_name,
                   l.name AS league_name,
                   s.name AS season_name
            FROM achievements AS a
            JOIN achievement_types AS t ON t.id = a.type_id
            JOIN leagues AS l ON l.id = a.league_id
            JOIN seasons AS s ON s.id = a.season_id
            """)).fetchall()

    for row in rows:
        achievement_id, current_title, type_name, league_name, season_name = row
        legacy = f"{type_name} {league_name} {season_name}"
        if (current_title or "").strip() == legacy.strip():
            bind.execute(
                sa.text("UPDATE achievements SET title = :new WHERE id = :id"),
                {"new": type_name, "id": achievement_id},
            )


def downgrade() -> None:
    """Restore the legacy verbose pattern for rows that match the new short form.

    This is best-effort: if the user has since edited the title manually
    we won't touch it.
    """

    bind = op.get_bind()

    rows = bind.execute(sa.text("""
            SELECT a.id AS achievement_id,
                   a.title AS achievement_title,
                   t.name AS type_name,
                   l.name AS league_name,
                   s.name AS season_name
            FROM achievements AS a
            JOIN achievement_types AS t ON t.id = a.type_id
            JOIN leagues AS l ON l.id = a.league_id
            JOIN seasons AS s ON s.id = a.season_id
            """)).fetchall()

    for row in rows:
        achievement_id, current_title, type_name, league_name, season_name = row
        if (current_title or "").strip() == (type_name or "").strip():
            verbose = f"{type_name} {league_name} {season_name}"
            bind.execute(
                sa.text("UPDATE achievements SET title = :new WHERE id = :id"),
                {"new": verbose, "id": achievement_id},
            )
