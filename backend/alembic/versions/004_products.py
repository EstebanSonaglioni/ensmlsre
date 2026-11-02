"""Invitaciones persistidas y publicaciones de productos.

Revision ID: 004_products
Revises: 003_stores
Create Date: 2026-11-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_products"
down_revision: str | Sequence[str] | None = "003_stores"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "store_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.UniqueConstraint("store_id", "email"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column(
            "seller_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("subcategory", sa.String(), nullable=False),
        sa.Column("image_path", sa.String(), nullable=False),
        sa.Column("paused", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "product_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False
        ),
        sa.Column(
            "asker_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "product_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("product_questions.id"),
            nullable=False,
        ),
        sa.Column(
            "responder_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("question_id"),
    )


def downgrade() -> None:
    op.drop_table("product_answers")
    op.drop_table("product_questions")
    op.drop_table("products")
    op.drop_table("store_invitations")
