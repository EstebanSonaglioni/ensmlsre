"""Nombre y foto de perfil.

Revision ID: 008_user_profile
Revises: 007_product_net_profit
Create Date: 2026-11-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_user_profile"
down_revision: str | Sequence[str] | None = "007_product_net_profit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "display_name",
            sa.String(),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "users",
        sa.Column("avatar_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "avatar_path")
    op.drop_column("users", "display_name")
