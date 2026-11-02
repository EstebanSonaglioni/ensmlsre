"""Ganancia neta por unidad en productos.

Revision ID: 007_product_net_profit
Revises: 006_order_tracking
Create Date: 2026-11-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_product_net_profit"
down_revision: str | Sequence[str] | None = "006_order_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "net_profit",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("products", "net_profit")
