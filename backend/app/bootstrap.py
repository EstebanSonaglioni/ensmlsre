"""Prepara el schema en host SQLite. En Postgres usa Alembic (Compose)."""

from app.core.db import get_engine, is_sqlite
from app.models import Base


def prepare_schema() -> None:
    if not is_sqlite():
        return
    Base.metadata.create_all(get_engine())


def main() -> None:
    prepare_schema()


if __name__ == "__main__":
    main()
