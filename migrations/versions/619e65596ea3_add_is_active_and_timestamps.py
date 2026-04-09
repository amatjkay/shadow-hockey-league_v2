"""add_is_active_and_timestamps

Revision ID: 619e65596ea3
Revises: af0b8338a403
Create Date: 2026-04-09 11:52:17.641684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '619e65596ea3'
down_revision: Union[str, None] = 'af0b8338a403'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Achievement timestamps (only columns not yet existing)
    if dialect == 'sqlite':
        with op.batch_alter_table('achievements') as batch_op:
            batch_op.add_column(
                sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
            )
            batch_op.add_column(
                sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
            )
            batch_op.create_index('idx_achievement_manager', ['manager_id'])
            batch_op.create_index('idx_achievement_type', ['type_id'])
            batch_op.create_index('idx_achievement_league', ['league_id'])
            batch_op.create_index('idx_achievement_season', ['season_id'])
            batch_op.create_index('idx_achievement_points', ['final_points'])
    else:
        op.add_column(
            'achievements',
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
        )
        op.add_column(
            'achievements',
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
        )
        op.create_index('idx_achievement_manager', 'achievements', ['manager_id'])
        op.create_index('idx_achievement_type', 'achievements', ['type_id'])
        op.create_index('idx_achievement_league', 'achievements', ['league_id'])
        op.create_index('idx_achievement_season', 'achievements', ['season_id'])
        op.create_index('idx_achievement_points', 'achievements', ['final_points'])

    # Other indexes (if not yet existing)
    try:
        op.create_index('idx_country_search', 'countries', ['code', 'name'])
    except Exception:
        pass  # Index may already exist
    try:
        op.create_index('idx_manager_name', 'managers', ['name'])
    except Exception:
        pass


def downgrade() -> None:
    # Drop indexes
    try:
        op.drop_index('idx_achievement_points', 'achievements')
    except Exception:
        pass
    try:
        op.drop_index('idx_achievement_season', 'achievements')
    except Exception:
        pass
    try:
        op.drop_index('idx_achievement_league', 'achievements')
    except Exception:
        pass
    try:
        op.drop_index('idx_achievement_type', 'achievements')
    except Exception:
        pass
    try:
        op.drop_index('idx_achievement_manager', 'achievements')
    except Exception:
        pass
    try:
        op.drop_index('idx_manager_name', 'managers')
    except Exception:
        pass
    try:
        op.drop_index('idx_country_search', 'countries')
    except Exception:
        pass

    # Drop columns
    try:
        op.drop_column('achievements', 'updated_at')
    except Exception:
        pass
    try:
        op.drop_column('achievements', 'created_at')
    except Exception:
        pass
