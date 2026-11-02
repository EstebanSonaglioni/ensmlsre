import uuid

from fastapi.testclient import TestClient


def test_buyer_creates_store_with_unique_name_and_becomes_admin(
    client: TestClient,
) -> None:
    email = f"ana.tienda.{uuid.uuid4().hex}@example.com"
    name = f"Tienda de Ana {uuid.uuid4().hex[:8]}"
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "secreto-valido"},
    )
    assert registered.status_code == 201
    token = registered.json()["access_token"]

    response = client.post(
        "/stores",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == name
    assert body["role"] == "admin"
    assert "password" not in body


def _register_and_token(client: TestClient) -> str:
    registered = client.post(
        "/auth/register",
        json={
            "email": f"ana.tienda.{uuid.uuid4().hex}@example.com",
            "password": "secreto-valido",
        },
    )
    assert registered.status_code == 201
    return registered.json()["access_token"]


def test_create_store_duplicate_name_returns_generic_error(
    client: TestClient,
) -> None:
    name = f"Tienda duplicada {uuid.uuid4().hex}"
    first = client.post(
        "/stores",
        json={"name": name},
        headers={"Authorization": f"Bearer {_register_and_token(client)}"},
    )
    assert first.status_code == 201

    response = client.post(
        "/stores",
        json={"name": name},
        headers={"Authorization": f"Bearer {_register_and_token(client)}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "No se pudo crear la tienda"}
    assert "role" not in response.json()


def test_create_store_invalid_name_returns_generic_error(
    client: TestClient,
) -> None:
    response = client.post(
        "/stores",
        json={"name": ""},
        headers={"Authorization": f"Bearer {_register_and_token(client)}"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}
    assert "role" not in response.json()


