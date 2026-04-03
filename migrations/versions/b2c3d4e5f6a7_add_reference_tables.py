"""add reference tables achievement_types, leagues, seasons

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-03
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create achievement_types reference table
    op.create_table(
        "achievement_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("base_points_l1", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("base_points_l2", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(
        op.f("ix_achievement_types_code"), "achievement_types", ["code"], unique=False
    )

    # Create leagues reference table
    op.create_table(
        "leagues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_leagues_code"), "leagues", ["code"], unique=False)

    # Create seasons reference table
    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("multiplier", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_seasons_code"), "seasons", ["code"], unique=False)

    # Seed reference data
    # Achievement types with base points matching the hardcoded values
    op.bulk_insert(
        sa.table(
            "achievement_types",
            sa.column("code", sa.String),
            sa.column("name", sa.String),
            sa.column("base_points_l1", sa.Integer),
            sa.column("base_points_l2", sa.Integer),
        ),
        [
            {"code": "TOP1", "name": "TOP1", "base_points_l1": 800, "base_points_l2": 300},
            {"code": "TOP2", "name": "TOP2", "base_points_l1": 550, "base_points_l2": 200},
            {"code": "TOP3", "name": "TOP3", "base_points_l1": 450, "base_points_l2": 100},
            {"code": "BEST", "name": "Best regular", "base_points_l1": 50, "base_points_l2": 40},
            {"code": "R3", "name": "Round 3", "base_points_l1": 30, "base_points_l2": 20},
            {"code": "R1", "name": "Round 1", "base_points_l1": 10, "base_points_l2": 5},
        ],
    )

    # Leagues
    op.bulk_insert(
        sa.table(
            "leagues",
            sa.column("code", sa.String),
            sa.column("name", sa.String),
        ),
        [
            {"code": "1", "name": "League 1"},
            {"code": "2", "name": "League 2"},
        ],
    )

    # Seasons with multipliers matching the hardcoded values
    op.bulk_insert(
        sa.table(
            "seasons",
            sa.column("code", sa.String),
            sa.column("name", sa.String),
            sa.column("multiplier", sa.Float),
            sa.column("is_active", sa.Boolean),
        ),
        [
            {"code": "25/26", "name": "Season 2025/26", "multiplier": 1.00, "is_active": True},
            {"code": "24/25", "name": "Season 2024/25", "multiplier": 0.95, "is_active": False},
            {"code": "23/24", "name": "Season 2023/24", "multiplier": 0.90, "is_active": False},
            {"code": "22/23", "name": "Season 2022/23", "multiplier": 0.85, "is_active": False},
            {"code": "21/22", "name": "Season 2021/22", "multiplier": 0.80, "is_active": False},
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_seasons_code"), table_name="seasons")
    op.drop_table("seasons")
    op.drop_index(op.f("ix_leagues_code"), table_name="leagues")
    op.drop_table("leagues")
    op.drop_index(op.f("ix_achievement_types_code"), table_name="achievement_types")
    op.drop_table("achievement_types")
