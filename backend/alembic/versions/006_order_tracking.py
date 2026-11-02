"""ETA, mensajes de orden y notificaciones.

Revision ID: 006_order_tracking
Revises: 005_commerce
Create Date: 2026-11-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_order_tracking"
down_revision: str | Sequence[str] | None = "005_commerce"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sells",
        sa.Column("eta_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "sell_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "sell_id",
            sa.Integer(),
            sa.ForeignKey("sells.id"),
            nullable=False,
        ),
        sa.Column(
            "sender_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("body", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sell_messages_sell_id", "sell_messages", ["sell_id"])
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "sell_id",
            sa.Integer(),
            sa.ForeignKey("sells.id"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('mensaje', 'estado')",
            name="notifications_kind_check",
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_sell_messages_sell_id", table_name="sell_messages")
    op.drop_table("sell_messages")
    op.drop_column("sells", "eta_at")
