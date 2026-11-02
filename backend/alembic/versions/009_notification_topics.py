"""Notificaciones de pregunta, respuesta y venta.

Revision ID: 009_notification_topics
Revises: 008_user_profile
Create Date: 2026-11-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009_notification_topics"
down_revision: str | Sequence[str] | None = "008_user_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("notifications_kind_check", "notifications", type_="check")
    op.alter_column(
        "notifications",
        "sell_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column(
        "notifications",
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id"),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "notifications_kind_check",
        "notifications",
        "kind IN ('mensaje', 'estado', 'pregunta', 'respuesta', 'venta')",
    )


def downgrade() -> None:
    op.drop_constraint("notifications_kind_check", "notifications", type_="check")
    op.drop_column("notifications", "product_id")
    op.alter_column(
        "notifications",
        "sell_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_check_constraint(
        "notifications_kind_check",
        "notifications",
        "kind IN ('mensaje', 'estado')",
    )
