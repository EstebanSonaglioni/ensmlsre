import importlib
import uuid

import app.main as main
import app.routers.auth as auth
from fastapi.testclient import TestClient


def _restarted_client() -> TestClient:
    importlib.reload(auth)
    importlib.reload(main)
    return TestClient(main.app)


def test_login_after_app_restart_enters_with_same_account(
    client: TestClient,
) -> None:
    payload = {
        "email": f"ana.persist.login.{uuid.uuid4().hex}@example.com",
        "password": "secreto-valido",
    }
    registered = client.post("/auth/register", json=payload)
    assert registered.status_code == 201

    response = _restarted_client().post("/auth/login", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["role"] == "comprador"
    assert body["access_token"]
    assert "password" not in body
    assert "password_hash" not in body
