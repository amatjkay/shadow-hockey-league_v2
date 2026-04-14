"""add_parent_code_to_leagues

Revision ID: 8a3279741758
Revises: 1fdc901fa43e
Create Date: 2026-04-14 22:01:10.685253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


# revision identifiers, used by Alembic.
revision: str = '8a3279741758'
down_revision: Union[str, None] = '1fdc901fa43e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table('leagues', schema=None) as batch_op:
        # Add parent_code column
        batch_op.add_column(sa.Column('parent_code', sa.String(10), nullable=True))

        # Create foreign key constraint (self-referential)
        batch_op.create_foreign_key(
            'fk_league_parent_code',
            'leagues',
            ['parent_code'], ['code'],
            ondelete='SET NULL'
        )

        # Create index for parent_code
        batch_op.create_index('ix_leagues_parent_code', ['parent_code'])

    # Populate parent_code for existing data
    # Leagues 2.1 and 2.2 are subleagues of league 2
    op.execute("UPDATE leagues SET parent_code = '2' WHERE code IN ('2.1', '2.2')")
    # Leagues 1 and 2 have no parent
    op.execute("UPDATE leagues SET parent_code = NULL WHERE code IN ('1', '2')")


def downgrade() -> None:
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table('leagues', schema=None) as batch_op:
        # Drop index
        batch_op.drop_index('ix_leagues_parent_code')

        # Drop foreign key (SQLite requires recreating table)
        batch_op.drop_constraint('fk_league_parent_code', type_='foreignkey')

        # Drop column
        batch_op.drop_column('parent_code')
