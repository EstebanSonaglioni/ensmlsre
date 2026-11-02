"""Entrega, saldo del vendedor y tabla sells.

Revision ID: 005_commerce
Revises: 004_products
Create Date: 2026-11-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_commerce"
down_revision: str | Sequence[str] | None = "004_products"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "ships",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "pickup",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "balance",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_table(
        "sells",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "buyer_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "seller_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id"),
            nullable=False,
        ),
        sa.Column(
            "store_id",
            sa.Integer(),
            sa.ForeignKey("stores.id"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("fulfillment", sa.String(), nullable=False),
        sa.Column("payment_method", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("checkout_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "fulfillment IN ('envio', 'retiro')",
            name="sells_fulfillment_check",
        ),
        sa.CheckConstraint(
            "status IN ('en_carrito', 'en_curso', 'en_viaje', "
            "'esperando_retiro', 'completada', 'cancelada', 'reembolsada')",
            name="sells_status_check",
        ),
    )
    op.create_index("ix_sells_buyer_status", "sells", ["buyer_user_id", "status"])
    op.create_index("ix_sells_seller_status", "sells", ["seller_user_id", "status"])
    op.create_index(
        "ix_sells_cart_product",
        "sells",
        ["buyer_user_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("status = 'en_carrito'"),
    )


def downgrade() -> None:
    op.drop_index("ix_sells_cart_product", table_name="sells")
    op.drop_index("ix_sells_seller_status", table_name="sells")
    op.drop_index("ix_sells_buyer_status", table_name="sells")
    op.drop_table("sells")
    op.drop_column("users", "balance")
    op.drop_column("products", "pickup")
    op.drop_column("products", "ships")
