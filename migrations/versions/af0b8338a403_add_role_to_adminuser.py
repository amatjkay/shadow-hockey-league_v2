"""add_role_to_adminuser

Revision ID: af0b8338a403
Revises: c8a1f0cd030d
Create Date: 2026-04-08 23:25:10.575854

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af0b8338a403'
down_revision: Union[str, None] = 'c8a1f0cd030d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'admin_users',
        sa.Column('role', sa.String(20), nullable=False, server_default='moderator',
                  comment='super_admin: full access, admin: CRUD, moderator: view/edit only')
    )
    op.create_index('ix_admin_users_role', 'admin_users', ['role'])


def downgrade() -> None:
    op.drop_index('ix_admin_users_role', 'admin_users')
    op.drop_column('admin_users', 'role')
