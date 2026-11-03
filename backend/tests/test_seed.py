from pathlib import Path

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models.product import Product, ProductQuestion
from app.models.sell import Sell
from app.models.user import User
from app.seed import DEMO_BOSS, DEMO_BUYERS, DEMO_SELLERS, DEMO_STORE, seed_demo
from fastapi.testclient import TestClient
from sqlalchemy import func, select

_PASSWORD = "mlsre-demo"


def _session():
    return get_session_factory()()


def test_seed_is_idempotent_and_creates_demo_users() -> None:
    session = _session()
    try:
        second = seed_demo(session)
        emails = {
            session.scalar(select(User.email).where(User.email == email))
            for email in (DEMO_BOSS, *DEMO_SELLERS, *DEMO_BUYERS)
        }
        bosses = session.scalars(select(User).where(User.email == DEMO_BOSS)).all()
    finally:
        session.close()
    assert emails == {DEMO_BOSS, *DEMO_SELLERS, *DEMO_BUYERS}
    assert len(bosses) == 1
    assert second is False


def test_seed_products_use_image_stems_and_split_sellers() -> None:
    session = _session()
    try:
        ventas1 = session.scalar(select(User).where(User.email == DEMO_SELLERS[0]))
        ventas2 = session.scalar(select(User).where(User.email == DEMO_SELLERS[1]))
        assert ventas1 is not None and ventas2 is not None
        names = set(
            session.scalars(
                select(Product.name).where(
                    Product.seller_user_id.in_((ventas1.id, ventas2.id))
                )
            ).all()
        )
        owned1 = session.scalar(
            select(func.count(Product.id)).where(Product.seller_user_id == ventas1.id)
        )
        owned2 = session.scalar(
            select(func.count(Product.id)).where(Product.seller_user_id == ventas2.id)
        )
    finally:
        session.close()
    assert "aceite" in names
    assert "chocolate" in names
    assert owned1 and owned2
    assert abs(int(owned1) - int(owned2)) <= 1


def test_seed_product_image_matches_source_file(client: TestClient) -> None:
    session = _session()
    try:
        seed_demo(session)
        product = session.scalar(select(Product).where(Product.name == "aceite"))
        assert product is not None
        assert product.image_path == "aceite.jpeg"
        stored = Path(get_settings().PRODUCT_IMAGES_DIR) / "aceite.jpeg"
        source = (
            Path(__file__).resolve().parents[1] / "seed" / "products" / "aceite.jpeg"
        )
        assert stored.is_file()
        assert stored.read_bytes() == source.read_bytes()
        product_id = product.id
    finally:
        session.close()
    login = client.post(
        "/auth/login",
        json={"email": DEMO_BUYERS[0], "password": _PASSWORD},
    )
    assert login.status_code == 200
    image = client.get(
        f"/products/{product_id}/image",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert image.status_code == 200
    assert image.content.startswith(b"\xff\xd8")


def test_seed_completed_sales_span_ninety_days() -> None:
    session = _session()
    try:
        rows = session.scalars(select(Sell).where(Sell.status == "completada")).all()
        store_sales = [
            row
            for row in rows
            if row.product.store.name == DEMO_STORE
        ]
        updated = [row.updated_at for row in store_sales]
    finally:
        session.close()
    assert len(store_sales) >= 60
    span = max(updated) - min(updated)
    assert span.days >= 80


def test_seed_has_open_orders_questions_and_login(client: TestClient) -> None:
    session = _session()
    try:
        ventas = session.scalars(
            select(User.id).where(User.email.in_(DEMO_SELLERS))
        ).all()
        open_count = session.scalar(
            select(func.count(Sell.id)).where(
                Sell.seller_user_id.in_(ventas),
                Sell.status.in_(("en_curso", "en_viaje", "esperando_retiro")),
            )
        )
        questions = session.scalar(select(func.count(ProductQuestion.id)))
    finally:
        session.close()
    assert int(open_count or 0) >= 3
    assert int(questions or 0) >= 10

    login = client.post(
        "/auth/login",
        json={"email": DEMO_BOSS, "password": _PASSWORD},
    )
    assert login.status_code == 200
    assert login.json()["email"] == DEMO_BOSS
    assert login.json()["role"] == "vendedor"


def test_seed_rejects_wrong_password(client: TestClient) -> None:
    session = _session()
    try:
        assert session.scalar(select(User.id).where(User.email == DEMO_BUYERS[0]))
    finally:
        session.close()
    login = client.post(
        "/auth/login",
        json={"email": DEMO_BUYERS[0], "password": "no-es-la-clave"},
    )
    assert login.status_code == 401
