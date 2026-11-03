from fastapi.testclient import TestClient


def test_cors_allows_frontend_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://evil.example"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") != "http://evil.example"


def test_cors_allows_hackerrank_preview_origin(client: TestClient) -> None:
    origin = "https://abc.projects.hackerrank.net"
    response = client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_not_found_returns_generic_spanish_detail(client: TestClient) -> None:
    response = client.get("/no-existe")
    assert response.status_code == 404
    body = response.json()
    assert body == {"detail": "Recurso no encontrado"}
    assert "traceback" not in str(body).lower()
    assert "stack" not in str(body).lower()


def test_method_not_allowed_returns_generic_detail(client: TestClient) -> None:
    response = client.post("/health")
    assert response.status_code == 405
    assert response.json() == {"detail": "Método no permitido"}


def test_oversized_body_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/health",
        headers={"Content-Length": str(1_000_001)},
        content=b"x",
    )
    assert response.status_code == 413
    assert response.json() == {
        "detail": "El cuerpo de la solicitud es demasiado grande"
    }


def test_responses_set_nosniff(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
