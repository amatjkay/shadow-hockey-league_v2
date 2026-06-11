"""inline league code unique

Revision ID: 3f6f9ed6c154
Revises: a4f1e9b2c5d7
Create Date: 2026-05-13 21:58:30.261310

TIK-98 follow-up to TIK-95. ``models.py::League.code`` previously used
``unique=True, index=True``, which made SQLAlchemy emit only a separate
``CREATE UNIQUE INDEX ix_leagues_code`` (no inline ``UNIQUE (code)``).
On Postgres that breaks ``db.create_all()`` because the self-referential
FK ``leagues.parent_code -> leagues.code`` is verified against the
referent's uniqueness *during* ``CREATE TABLE leagues``, before the
separate index is created.

The fix in ``models.py`` switches ``code`` to plain ``unique=True``
(inline ``UNIQUE`` constraint, no separate index). This migration aligns
the live schema with the new metadata by dropping the now-redundant
``ix_leagues_code`` index — the inline ``UNIQUE (code)`` constraint was
already created by revision ``b2c3d4e5f6a7`` (and is also present on
SQLite ``dev.db`` via the table copy in ``8a3279741758``).
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "3f6f9ed6c154"
down_revision: Union[str, None] = "a4f1e9b2c5d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch_alter_table works on both Postgres (direct ``DROP INDEX``) and
    # SQLite (no table copy is needed for a pure index drop).
    bind = op.get_bind()
    indexes = {index["name"] for index in inspect(bind).get_indexes("leagues")}
    if "ix_leagues_code" in indexes:
        with op.batch_alter_table("leagues", schema=None) as batch_op:
            batch_op.drop_index("ix_leagues_code")


def downgrade() -> None:
    # Restore the original non-unique index created by revision
    # ``b2c3d4e5f6a7`` (``op.create_index(..., unique=False)``).
    with op.batch_alter_table("leagues", schema=None) as batch_op:
        batch_op.create_index("ix_leagues_code", ["code"], unique=False)
