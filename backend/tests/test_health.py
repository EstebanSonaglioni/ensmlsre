from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_does_not_require_auth(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert "www-authenticate" not in {key.lower() for key in response.headers}


def test_health_propagates_request_id(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "test-request-id"})
    assert response.headers["x-request-id"] == "test-request-id"
