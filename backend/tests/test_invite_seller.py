import uuid

from fastapi.testclient import TestClient


def _register(client: TestClient) -> tuple[str, str]:
    email = f"ana.invite.{uuid.uuid4().hex}@example.com"
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "secreto-valido"},
    )
    assert registered.status_code == 201
    return email, registered.json()["access_token"]


def _create_store(client: TestClient, token: str) -> str:
    store_name = f"Tienda invite {uuid.uuid4().hex[:8]}"
    created = client.post(
        "/stores",
        json={"name": store_name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 201
    return store_name


def test_store_admin_invites_by_email_creates_invitation(
    client: TestClient,
) -> None:
    _admin_email, token = _register(client)
    store_name = _create_store(client, token)

    invitee = f"vendedor.{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/stores/invitations",
        json={"email": invitee, "store": store_name},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == invitee
    assert body["store"] == store_name
    assert "password" not in body


def test_invitee_sees_pending_invitation_when_logged_in(
    client: TestClient,
) -> None:
    _admin_email, admin_token = _register(client)
    store_name = _create_store(client, admin_token)
    invitee_email, invitee_token = _register(client)

    invited = client.post(
        "/stores/invitations",
        json={"email": invitee_email, "store": store_name},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert invited.status_code == 201

    response = client.get(
        "/stores/invitations",
        headers={"Authorization": f"Bearer {invitee_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"] == [{"email": invitee_email, "store": store_name}]


def test_admin_does_not_see_invitation_sent_to_someone_else(
    client: TestClient,
) -> None:
    _admin_email, admin_token = _register(client)
    store_name = _create_store(client, admin_token)
    client.post(
        "/stores/invitations",
        json={"email": f"otro.{uuid.uuid4().hex}@example.com", "store": store_name},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = client.get(
        "/stores/invitations",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_non_admin_cannot_invite_to_store(client: TestClient) -> None:
    _admin_email, admin_token = _register(client)
    store_name = _create_store(client, admin_token)
    _other_email, other_token = _register(client)

    response = client.post(
        "/stores/invitations",
        json={"email": f"vendedor.{uuid.uuid4().hex}@example.com", "store": store_name},
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "No se pudo crear la invitación"}


def test_invite_invalid_email_returns_generic_error(client: TestClient) -> None:
    _admin_email, token = _register(client)
    store_name = _create_store(client, token)

    response = client.post(
        "/stores/invitations",
        json={"email": "no-es-un-email", "store": store_name},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}

    listed = client.get(
        "/stores/invitations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.json()["total"] == 0


def test_invitee_accepts_invitation_and_joins_store(client: TestClient) -> None:
    _admin_email, admin_token = _register(client)
    store_name = _create_store(client, admin_token)
    invitee_email, invitee_token = _register(client)
    invited = client.post(
        "/stores/invitations",
        json={"email": invitee_email, "store": store_name},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert invited.status_code == 201

    response = client.post(
        "/stores/invitations/accept",
        json={"store": store_name},
        headers={"Authorization": f"Bearer {invitee_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"store": store_name, "role": "vendedor"}
    stores = client.get("/stores", headers={"Authorization": f"Bearer {invitee_token}"})
    assert stores.status_code == 200
    assert any(
        item["name"] == store_name and item["role"] == "vendedor"
        for item in stores.json()["items"]
    )
    pending = client.get(
        "/stores/invitations",
        headers={"Authorization": f"Bearer {invitee_token}"},
    )
    assert pending.json()["total"] == 0


def test_accept_invitation_without_invite_returns_generic_error(
    client: TestClient,
) -> None:
    _email, token = _register(client)
    response = client.post(
        "/stores/invitations/accept",
        json={"store": "No existe"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "No se pudo aceptar la invitación"}


def test_invite_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/stores/invitations",
        json={"email": "alguien@example.com", "store": "Tienda"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "No se pudo completar la solicitud"}
