"""Tiendas y membresías persistidas.

Revision ID: 003_stores
Revises: 002_users
Create Date: 2026-11-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_stores"
down_revision: str | Sequence[str] | None = "002_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "store_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.UniqueConstraint("store_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("store_memberships")
    op.drop_table("stores")
