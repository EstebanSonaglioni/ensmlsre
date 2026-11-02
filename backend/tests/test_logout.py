import uuid

from fastapi.testclient import TestClient

_CSRF = {"X-CSRF-Token": "1"}


def test_logout_revokes_token_and_clears_session(client: TestClient) -> None:
    registered = client.post(
        "/auth/register",
        json={
            "email": f"ana.logout.{uuid.uuid4().hex}@example.com",
            "password": "secreto-valido",
        },
    )
    assert registered.status_code == 201
    token = registered.json()["access_token"]

    response = client.post("/auth/logout", headers=_CSRF)

    assert response.status_code == 204
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "refresh_token=" in set_cookie
    assert "max-age=0" in set_cookie or "max-age=0;" in set_cookie

    me = client.get("/auth/me")
    assert me.status_code == 401
    assert me.json() == {"detail": "No se pudo completar la solicitud"}
    assert "access_token" not in me.json()

    stores = client.get("/stores", headers={"Authorization": f"Bearer {token}"})
    assert stores.status_code == 401
    assert stores.json() == {"detail": "No se pudo completar la solicitud"}


def test_logout_without_cookie_returns_generic_error(client: TestClient) -> None:
    client.cookies.clear()
    response = client.post("/auth/logout", headers=_CSRF)

    assert response.status_code == 401
    assert response.json() == {"detail": "No se pudo completar la solicitud"}


def test_logout_without_csrf_returns_generic_error(client: TestClient) -> None:
    registered = client.post(
        "/auth/register",
        json={
            "email": f"ana.csrf.{uuid.uuid4().hex}@example.com",
            "password": "secreto-valido",
        },
    )
    assert registered.status_code == 201

    response = client.post("/auth/logout")

    assert response.status_code == 403
    assert response.json() == {"detail": "No se pudo completar la solicitud"}
    me = client.get("/auth/me")
    assert me.status_code == 200
