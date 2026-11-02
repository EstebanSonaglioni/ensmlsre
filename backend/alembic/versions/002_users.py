"""Usuarios persistidos.

Revision ID: 002_users
Revises: 001_initial
Create Date: 2026-11-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_users"
down_revision: str | Sequence[str] | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.UniqueConstraint("email"),
    )


def downgrade() -> None:
    op.drop_table("users")
