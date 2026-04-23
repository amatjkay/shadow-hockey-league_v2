"""add_icon_path_to_achievement_types

Revision ID: 58667e02fd0d
Revises: 8a3279741758
Create Date: 2026-04-14 22:11:36.534506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58667e02fd0d'
down_revision: Union[str, None] = '8a3279741758'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'achievement_types',
        sa.Column('icon_path', sa.String(100), nullable=True, server_default='/static/img/cups/default.svg')
    )


def downgrade() -> None:
    op.drop_column('achievement_types', 'icon_path')
