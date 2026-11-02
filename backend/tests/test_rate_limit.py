import uuid

from fastapi.testclient import TestClient


def test_login_is_limited_to_five_attempts_per_minute(client: TestClient) -> None:
    payload = {
        "email": f"ana.limit.{uuid.uuid4().hex}@example.com",
        "password": "secreto-valido",
    }
    statuses = []
    for _ in range(6):
        statuses.append(client.post("/auth/login", json=payload).status_code)
    assert statuses[:5] == [401, 401, 401, 401, 401]
    assert statuses[5] == 429
    assert client.post("/auth/login", json=payload).json() == {
        "detail": "No se pudo completar la solicitud"
    }
