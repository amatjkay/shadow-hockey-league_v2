"""Add name field to countries

Revision ID: 4349a74b0533
Revises: 695116ad35a1
Create Date: 2026-04-02 11:44:28.748155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4349a74b0533'
down_revision: Union[str, None] = '695116ad35a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add name column to countries table
    op.add_column('countries', sa.Column('name', sa.String(length=100), nullable=False, server_default='Unknown'))


def downgrade() -> None:
    # Remove name column from countries table
    op.drop_column('countries', 'name')
