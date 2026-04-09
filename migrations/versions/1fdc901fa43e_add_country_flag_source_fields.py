"""add_country_flag_source_fields

Revision ID: 1fdc901fa43e
Revises: 619e65596ea3
Create Date: 2026-04-09 12:54:02.982191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1fdc901fa43e'
down_revision: Union[str, None] = '619e65596ea3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add flag_source_type and flag_url columns to countries table."""
    op.add_column(
        'countries',
        sa.Column('flag_source_type', sa.String(20), nullable=False, server_default='local',
                  comment="Flag source type: 'local' or 'api'")
    )
    op.add_column(
        'countries',
        sa.Column('flag_url', sa.String(200), nullable=True,
                  comment="Flag URL from API (e.g., FlagCDN) or custom URL")
    )


def downgrade() -> None:
    """Remove flag source fields from countries table."""
    op.drop_column('countries', 'flag_url')
    op.drop_column('countries', 'flag_source_type')
