"""Esquema inicial vacío.

Revision ID: 001_initial
Revises:
Create Date: 2026-11-01

"""

from collections.abc import Sequence

revision: str = "001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
