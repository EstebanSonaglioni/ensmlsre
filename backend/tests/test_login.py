import uuid

from app.core.db import get_session_factory
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import select


def test_login_with_existing_account_enters(client: TestClient) -> None:
    payload = {
        "email": f"ana.login.{uuid.uuid4().hex}@example.com",
        "password": "secreto-valido",
    }
    registered = client.post("/auth/register", json=payload)
    assert registered.status_code == 201

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["role"] == "comprador"
    assert body["access_token"]
    assert "password" not in body
    assert "password_hash" not in body


def test_login_unknown_email_or_wrong_password_returns_generic_error(
    client: TestClient,
) -> None:
    unknown = client.post(
        "/auth/login",
        json={"email": "nadie@example.com", "password": "secreto-valido"},
    )

    assert unknown.status_code == 401
    assert unknown.json() == {"detail": "No se pudo iniciar sesión"}
    assert "access_token" not in unknown.json()

    payload = {
        "email": f"ana.clave.{uuid.uuid4().hex}@example.com",
        "password": "secreto-valido",
    }
    registered = client.post("/auth/register", json=payload)
    assert registered.status_code == 201

    wrong = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "otra-clave"},
    )

    assert wrong.status_code == 401
    assert wrong.json() == {"detail": "No se pudo iniciar sesión"}
    assert "access_token" not in wrong.json()


def test_login_invalid_data_returns_generic_error(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "ana.invalida@example.com", "password": ""},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}
    assert "access_token" not in response.json()


def test_login_promotes_store_member_marked_as_buyer(client: TestClient) -> None:
    payload = {
        "email": f"ana.rol.{uuid.uuid4().hex}@example.com",
        "password": "secreto-valido",
    }
    registered = client.post("/auth/register", json=payload)
    assert registered.status_code == 201
    token = registered.json()["access_token"]
    created = client.post(
        "/stores",
        json={"name": f"Tienda rol {uuid.uuid4().hex[:8]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 201

    session = get_session_factory()()
    user = session.scalar(select(User).where(User.email == payload["email"]))
    assert user is not None
    user.role = "comprador"
    session.commit()
    session.close()

    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    assert response.json()["role"] == "vendedor"
    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["role"] == "vendedor"


