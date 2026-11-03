import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
_TEST_IMAGES = Path(__file__).resolve().parent / "_test_images"
_TEST_AVATARS = Path(__file__).resolve().parent / "_test_avatars"
_TEST_LOGS = Path(__file__).resolve().parent / "_test_logs"


def _load_root_env() -> None:
    if not _ROOT_ENV.exists():
        return
    for raw in _ROOT_ENV.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _for_host(url: str) -> str:
    if url.startswith("sqlite") or Path("/.dockerenv").exists():
        return url
    port = os.environ.get("POSTGRES_HOST_PORT", "5433")
    return url.replace("@db:5432", f"@localhost:{port}")


_load_root_env()
_pg_host_port = os.environ.get("POSTGRES_HOST_PORT", "5433")
if "DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = _for_host(os.environ["DATABASE_URL"])
if "MIGRATION_DATABASE_URL" in os.environ:
    os.environ["MIGRATION_DATABASE_URL"] = _for_host(
        os.environ["MIGRATION_DATABASE_URL"]
    )

os.environ.setdefault(
    "DATABASE_URL",
    f"postgresql+psycopg://mlsre_app:mlsre_app@localhost:{_pg_host_port}/mlsre",
)
os.environ.setdefault(
    "MIGRATION_DATABASE_URL",
    f"postgresql+psycopg://mlsre_migrate:mlsre_migrate@localhost:{_pg_host_port}/mlsre",
)
os.environ["JWT_SECRET"] = "test-secret-not-for-production-use"
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ["PRODUCT_IMAGES_DIR"] = str(_TEST_IMAGES)
os.environ["PROFILE_IMAGES_DIR"] = str(_TEST_AVATARS)
_TEST_LOGS.mkdir(parents=True, exist_ok=True)
os.environ["LOG_FILE"] = str(_TEST_LOGS / "app.log")

from app.core.db import get_session_factory  # noqa: E402
from app.core.rate_limit import reset_rate_limits  # noqa: E402
from app.main import app  # noqa: E402
from app.models.message import SellMessage  # noqa: E402
from app.models.notification import Notification  # noqa: E402
from app.models.product import Product, ProductAnswer, ProductQuestion  # noqa: E402
from app.models.refresh import RefreshSession  # noqa: E402
from app.models.sell import Sell  # noqa: E402
from app.models.store import Store, StoreInvitation, StoreMembership  # noqa: E402
from app.models.user import User  # noqa: E402
from app.seed import seed_demo  # noqa: E402

_CLEANUP_ORDER = (
    ProductAnswer,
    ProductQuestion,
    Notification,
    SellMessage,
    Sell,
    Product,
    StoreInvitation,
    StoreMembership,
    Store,
    RefreshSession,
    User,
)


def _max_id(session, model) -> int:
    return session.scalar(select(func.max(model.id))) or 0


def revert_rows_created_after(session, floors: dict[type, int]) -> None:
    for model in _CLEANUP_ORDER:
        session.execute(delete(model).where(model.id > floors[model]))
    session.commit()


@pytest.fixture(scope="session", autouse=True)
def _do_not_leave_test_rows_in_dev_db() -> None:
    session = get_session_factory()()
    try:
        seed_demo(session)
        floors = {model: _max_id(session, model) for model in _CLEANUP_ORDER}
    finally:
        session.close()
    yield
    session = get_session_factory()()
    try:
        revert_rows_created_after(session, floors)
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    reset_rate_limits()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, base_url="https://testserver")
