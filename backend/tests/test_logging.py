import json
import logging
from pathlib import Path

from app.core.config import get_settings
from fastapi.testclient import TestClient


def _flush_logs() -> None:
    for handler in logging.getLogger().handlers:
        handler.flush()


def test_request_writes_json_line_without_secrets(client: TestClient) -> None:
    log_path = Path(get_settings().LOG_FILE)
    before = log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    response = client.get(
        "/no-existe",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert response.status_code == 404
    _flush_logs()

    added = log_path.read_text(encoding="utf-8")[len(before) :]
    payloads = [json.loads(line) for line in added.splitlines() if line.strip()]
    request_logs = [item for item in payloads if item.get("event") == "request"]
    assert request_logs
    payload = request_logs[-1]
    assert payload["event"] == "request"
    assert payload["method"] == "GET"
    assert payload["path"] == "/no-existe"
    assert payload["status"] == 404
    assert "request_id" in payload
    assert "latency_ms" in payload
    dumped = json.dumps(payload)
    assert "secret-token" not in dumped
    assert "password" not in dumped
    assert "cookie" not in dumped.lower()


def test_health_does_not_write_access_log(client: TestClient) -> None:
    log_path = Path(get_settings().LOG_FILE)
    before = log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    response = client.get("/health")
    assert response.status_code == 200
    _flush_logs()

    added = log_path.read_text(encoding="utf-8")[len(before) :]
    assert '"path": "/health"' not in added
    assert '"event": "request"' not in added
