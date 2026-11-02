import uuid

import jwt
from fastapi.testclient import TestClient


def test_register_sets_httponly_refresh_cookie(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": f"ana.cookie.{uuid.uuid4().hex}@example.com",
            "password": "secreto-valido",
        },
    )

    assert response.status_code == 201
    access = response.json()["access_token"]
    refresh = response.cookies.get("refresh_token")
    assert refresh
    assert access != refresh
    access_payload = jwt.decode(access, options={"verify_signature": False})
    refresh_payload = jwt.decode(refresh, options={"verify_signature": False})
    assert access_payload["typ"] == "access"
    assert refresh_payload["typ"] == "refresh"
    assert access_payload["exp"] - access_payload["iat"] == 15 * 60
    assert refresh_payload["exp"] - refresh_payload["iat"] == 7 * 24 * 3600
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "refresh_token=" in set_cookie
    assert "httponly" in set_cookie
    assert "secure" in set_cookie
    assert "samesite=none" in set_cookie
    assert "password" not in set_cookie
    forbidden = client.get("/stores", headers={"Authorization": f"Bearer {refresh}"})
    assert forbidden.status_code == 401


def test_me_restores_session_from_refresh_cookie(client: TestClient) -> None:
    email = f"ana.sesion.{uuid.uuid4().hex}@example.com"
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "secreto-valido"},
    )
    assert registered.status_code == 201

    response = client.get("/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == email
    assert body["role"] == "comprador"
    assert body["access_token"]
    assert body["access_token"] != registered.cookies.get("refresh_token")
    restored = jwt.decode(body["access_token"], options={"verify_signature": False})
    assert restored["typ"] == "access"
    assert "password" not in body


def test_me_without_cookie_returns_generic_error(client: TestClient) -> None:
    client.cookies.clear()
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "No se pudo completar la solicitud"}
    assert "access_token" not in response.json()
