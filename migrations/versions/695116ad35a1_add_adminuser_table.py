"""Add AdminUser table

Revision ID: 695116ad35a1
Revises: d65f2c57c0a9
Create Date: 2026-04-02 10:20:32.484568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '695116ad35a1'
down_revision: Union[str, None] = 'd65f2c57c0a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create admin_users table
    op.create_table('admin_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    # Create index on username for faster lookups
    op.create_index(op.f('ix_admin_users_username'), 'admin_users', ['username'], unique=False)


def downgrade() -> None:
    # Drop index and table
    op.drop_index(op.f('ix_admin_users_username'), table_name='admin_users')
    op.drop_table('admin_users')
