import uuid

from fastapi.testclient import TestClient


def test_register_with_valid_data_enters_as_buyer(client: TestClient) -> None:
    email = f"ana.reg.{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "secreto-valido"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert body["role"] == "comprador"
    assert body["access_token"]
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_returns_generic_error_and_does_not_enter(
    client: TestClient,
) -> None:
    payload = {
        "email": f"ana.duplicada.{uuid.uuid4().hex}@example.com",
        "password": "secreto-valido",
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json() == {"detail": "No se pudo completar el registro"}
    assert "access_token" not in response.json()


def test_register_invalid_data_returns_generic_error_and_does_not_create_account(
    client: TestClient,
) -> None:
    email = f"ana.invalida.{uuid.uuid4().hex}@example.com"
    invalid = client.post(
        "/auth/register",
        json={"email": email, "password": ""},
    )

    assert invalid.status_code == 422
    assert invalid.json() == {"detail": "Los datos enviados no son válidos"}
    assert "access_token" not in invalid.json()

    created = client.post(
        "/auth/register",
        json={"email": email, "password": "secreto-valido"},
    )
    assert created.status_code == 201
    assert created.json()["email"] == email
    assert created.json()["csrf_token"]


def test_register_normalizes_email_and_rejects_invalid(client: TestClient) -> None:
    suffix = uuid.uuid4().hex
    mixed = f"Ana.Mix.{suffix}@Example.COM"
    response = client.post(
        "/auth/register",
        json={"email": mixed, "password": "secreto-valido"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == mixed.lower()

    invalid = client.post(
        "/auth/register",
        json={"email": "no-es-un-mail", "password": "secreto-valido"},
    )
    assert invalid.status_code == 422
    assert invalid.json() == {"detail": "Los datos enviados no son válidos"}
