import uuid
from io import BytesIO

from fastapi.testclient import TestClient

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
    b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _register(client: TestClient) -> tuple[str, str]:
    email = f"ana.perfil.{uuid.uuid4().hex}@example.com"
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "secreto-valido"},
    )
    assert registered.status_code == 201
    body = registered.json()
    assert body["display_name"] == ""
    assert body["has_avatar"] is False
    return email, body["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_update_profile_name(client: TestClient) -> None:
    _email, token = _register(client)
    response = client.patch(
        "/auth/profile",
        data={"display_name": "  Ana  "},
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["display_name"] == "Ana"
    assert body["has_avatar"] is False
    me = client.get("/auth/me")
    assert me.json()["display_name"] == "Ana"


def test_update_profile_photo(client: TestClient) -> None:
    _email, token = _register(client)
    missing = client.get("/auth/profile/image", headers=_auth(token))
    assert missing.status_code == 404
    updated = client.patch(
        "/auth/profile",
        data={"display_name": "Ana"},
        files={"image": ("foto.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(token),
    )
    assert updated.status_code == 200
    assert updated.json()["has_avatar"] is True
    image = client.get("/auth/profile/image", headers=_auth(token))
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content.startswith(b"\x89PNG")


def test_profile_name_too_long_is_rejected(client: TestClient) -> None:
    _email, token = _register(client)
    response = client.patch(
        "/auth/profile",
        data={"display_name": "a" * 81},
        headers=_auth(token),
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}


def test_profile_requires_auth(client: TestClient) -> None:
    response = client.patch("/auth/profile", data={"display_name": "Ana"})
    assert response.status_code == 401
    assert response.json() == {"detail": "No se pudo completar la solicitud"}


def test_create_store_marks_user_as_seller(client: TestClient) -> None:
    _email, token = _register(client)
    created = client.post(
        "/stores",
        json={"name": f"Tienda perfil {uuid.uuid4().hex[:8]}"},
        headers=_auth(token),
    )
    assert created.status_code == 201
    me = client.get("/auth/me")
    assert me.json()["role"] == "vendedor"
