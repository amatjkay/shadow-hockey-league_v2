"""backfill_season_start_end_years

Populate ``seasons.start_year`` / ``seasons.end_year`` for legacy rows
where these columns were ``NULL``.

Background
----------
The columns were added in :file:`a3e91f4c7b28_backfill_is_active_columns.py`
without a backfill: existing rows kept ``NULL``. That broke the
``/admin/api/seasons?league_id=…`` endpoint for League 2.1 / 2.2, which
applies a ``Season.start_year >= 2025`` filter (VR-004) — every legacy
row has ``start_year IS NULL`` so the season dropdown in the
"Add Achievement" admin modal came back empty (:doc:`TIK-76`).

Approach
--------
Parse :class:`models.Season` ``code`` (canonical form ``"YY/YY"``,
e.g. ``"25/26"``). Two-digit prefix ``YY``:

* ``YY < 70`` → ``20YY`` (covers 2000-2069, the realistic project range);
* otherwise → ``19YY`` (covers 1970-1999, kept for safety even though no
  current Season row falls in this bucket).

``end_year`` is ``start_year + 1``. Skip rows we cannot parse (defensive
no-op) and rows that already have a non-NULL ``start_year`` (idempotent
re-run, hot-fixed environments).

Revision ID: b5f2a8e1c34d
Revises: a3e91f4c7b28
Create Date: 2026-05-05 19:25:00.000000
"""

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b5f2a8e1c34d"
down_revision: Union[str, None] = "a3e91f4c7b28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CODE_RE = re.compile(r"^\s*(\d{2})\s*/\s*(\d{2})\s*$")


def _expand_two_digit_year(yy: int) -> int:
    """Map a two-digit year prefix to a four-digit year (pivot at 70)."""

    return 2000 + yy if yy < 70 else 1900 + yy


def upgrade() -> None:
    bind = op.get_bind()

    rows = bind.execute(
        sa.text(
            "SELECT id, code, start_year, end_year FROM seasons "
            "WHERE start_year IS NULL OR end_year IS NULL"
        )
    ).fetchall()

    for row in rows:
        season_id, code, start_year, end_year = row
        match = _CODE_RE.match(code or "")
        if not match:
            continue

        parsed_start = _expand_two_digit_year(int(match.group(1)))
        parsed_end = _expand_two_digit_year(int(match.group(2)))

        new_start = start_year if start_year is not None else parsed_start
        new_end = end_year if end_year is not None else parsed_end

        bind.execute(
            sa.text(
                "UPDATE seasons "
                "SET start_year = :start_year, end_year = :end_year "
                "WHERE id = :id"
            ),
            {"start_year": new_start, "end_year": new_end, "id": season_id},
        )


def downgrade() -> None:
    """Restore NULL for rows that match their parsed value.

    We only un-set rows whose current value matches what this migration
    would have written, so that any manually-curated values entered after
    the upgrade are preserved.
    """

    bind = op.get_bind()

    rows = bind.execute(sa.text("SELECT id, code, start_year, end_year FROM seasons")).fetchall()

    for row in rows:
        season_id, code, start_year, end_year = row
        match = _CODE_RE.match(code or "")
        if not match:
            continue

        parsed_start = _expand_two_digit_year(int(match.group(1)))
        parsed_end = _expand_two_digit_year(int(match.group(2)))

        if start_year == parsed_start and end_year == parsed_end:
            bind.execute(
                sa.text(
                    "UPDATE seasons " "SET start_year = NULL, end_year = NULL " "WHERE id = :id"
                ),
                {"id": season_id},
            )
