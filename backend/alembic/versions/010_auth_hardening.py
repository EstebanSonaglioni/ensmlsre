"""Hash de contraseñas y sesiones de refresh persistidas.

Revision ID: 010_auth_hardening
Revises: 009_notification_topics
Create Date: 2026-11-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from argon2 import PasswordHasher

revision: str = "010_auth_hardening"
down_revision: str | Sequence[str] | None = "009_notification_topics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_hasher = PasswordHasher()


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("auth_revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("jti"),
    )
    op.create_index(
        "ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"]
    )
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, password FROM users")).mappings()
    for row in rows:
        stored = row["password"]
        if stored.startswith("$argon2"):
            continue
        bind.execute(
            sa.text("UPDATE users SET password = :password WHERE id = :id"),
            {"password": _hasher.hash(stored), "id": row["id"]},
        )


def downgrade() -> None:
    op.drop_index("ix_refresh_sessions_user_id", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
    op.drop_column("users", "auth_revoked_at")
