import importlib
import uuid

import app.main as main
import app.routers.stores as stores
from app.core.db import get_session_factory
from app.models.store import Store, StoreMembership
from fastapi.testclient import TestClient
from sqlalchemy import select


def _register(client: TestClient) -> str:
    registered = client.post(
        "/auth/register",
        json={
            "email": f"ana.store.persist.{uuid.uuid4().hex}@example.com",
            "password": "secreto-valido",
        },
    )
    assert registered.status_code == 201
    return registered.json()["access_token"]


def test_created_store_is_saved_in_the_database(client: TestClient) -> None:
    token = _register(client)
    name = f"Tienda persistida {uuid.uuid4().hex[:8]}"
    created = client.post(
        "/stores",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 201

    session = get_session_factory()()
    try:
        store = session.scalar(select(Store).where(Store.name == name))
        assert store is not None
        membership = session.scalar(
            select(StoreMembership).where(StoreMembership.store_id == store.id)
        )
        assert membership is not None
        assert membership.role == "admin"
    finally:
        session.close()


def test_store_list_survives_app_reload(client: TestClient) -> None:
    token = _register(client)
    name = f"Tienda reload {uuid.uuid4().hex[:8]}"
    created = client.post(
        "/stores",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 201

    importlib.reload(stores)
    importlib.reload(main)
    restarted = TestClient(main.app, base_url="https://testserver")
    response = restarted.get(
        "/stores",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert any(
        item["name"] == name and item["role"] == "admin" for item in body["items"]
    )
