import uuid

from fastapi.testclient import TestClient


def _register(client: TestClient) -> str:
    registered = client.post(
        "/auth/register",
        json={
            "email": f"ana.list.{uuid.uuid4().hex}@example.com",
            "password": "secreto-valido",
        },
    )
    assert registered.status_code == 201
    return registered.json()["access_token"]


def test_list_stores_empty_when_none_associated(client: TestClient) -> None:
    token = _register(client)
    response = client.get("/stores", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1


def test_list_stores_returns_only_current_user_stores(client: TestClient) -> None:
    token_a = _register(client)
    token_b = _register(client)
    name_a = f"Tienda A {uuid.uuid4().hex[:8]}"
    created = client.post(
        "/stores",
        json={"name": name_a},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert created.status_code == 201
    client.post(
        "/stores",
        json={"name": f"Tienda B {uuid.uuid4().hex[:8]}"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    response = client.get("/stores", headers={"Authorization": f"Bearer {token_a}"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == name_a
    assert body["items"][0]["role"] == "admin"
    assert body["items"][0]["id"] > 0


def test_list_stores_filters_by_name(client: TestClient) -> None:
    token = _register(client)
    suffix = uuid.uuid4().hex[:8]
    client.post(
        "/stores",
        json={"name": f"Alpha {suffix}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/stores",
        json={"name": f"Beta {suffix}"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/stores",
        params={"q": "alpha"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"].startswith("Alpha")


def test_list_stores_requires_auth(client: TestClient) -> None:
    response = client.get("/stores")
    assert response.status_code == 401
    assert response.json() == {"detail": "No se pudo completar la solicitud"}
