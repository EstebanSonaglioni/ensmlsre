import time
from datetime import datetime

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from tests.test_products import (
    _create_product as _create_listed_product,
)
from tests.test_products import (
    _create_store as _create_listed_store,
)
from tests.test_sells import _auth, _create_product, _create_store, _register

WS_HEADERS = {"Origin": "http://localhost:3000"}


def _paid_envio(client: TestClient) -> tuple[str, str, str, str, int]:
    seller_email, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    buyer_email, buyer_token = _register(client)
    paid = client.post(
        "/sells/checkout",
        json={
            "payment_method": "tarjeta",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "fulfillment": "envio",
                }
            ],
        },
        headers=_auth(buyer_token),
    )
    assert paid.status_code == 200, paid.text
    sell_id = paid.json()["items"][0]["id"]
    return seller_email, seller_token, buyer_email, buyer_token, sell_id


def test_get_sell_other_buyer_not_found(client: TestClient) -> None:
    _s, seller_token, _b, buyer_token, sell_id = _paid_envio(client)
    _other, other_token = _register(client)
    response = client.get(f"/sells/{sell_id}", headers=_auth(other_token))
    assert response.status_code == 404
    assert response.json() == {"detail": "No se pudo completar la solicitud"}
    own = client.get(f"/sells/{sell_id}", headers=_auth(buyer_token))
    assert own.status_code == 200
    assert own.json()["id"] == sell_id
    assert own.json()["can_manage"] is False
    seller = client.get(f"/sells/{sell_id}", headers=_auth(seller_token))
    assert seller.status_code == 200
    assert seller.json()["can_manage"] is True


def test_message_requires_party_and_paid_order(client: TestClient) -> None:
    _s, seller_token, _b, buyer_token, sell_id = _paid_envio(client)
    _other, other_token = _register(client)
    denied = client.post(
        f"/sells/{sell_id}/messages",
        json={"body": "hola"},
        headers=_auth(other_token),
    )
    assert denied.status_code == 403

    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    cart = client.post(
        "/sells",
        json={"product_id": product["id"], "quantity": 1, "fulfillment": "retiro"},
        headers=_auth(buyer_token),
    )
    assert cart.status_code == 201
    cart_msg = client.post(
        f"/sells/{cart.json()['id']}/messages",
        json={"body": "hola"},
        headers=_auth(buyer_token),
    )
    assert cart_msg.status_code == 422
    assert cart_msg.json() == {"detail": "Los datos enviados no son válidos"}

    created = client.post(
        f"/sells/{sell_id}/messages",
        json={"body": "¿Cuándo sale?"},
        headers=_auth(buyer_token),
    )
    assert created.status_code == 201
    assert created.json()["body"] == "¿Cuándo sale?"
    assert created.json()["mine"] is True
    listed = client.get(f"/sells/{sell_id}/messages", headers=_auth(seller_token))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["mine"] is False
    own = client.get(f"/sells/{sell_id}/messages", headers=_auth(buyer_token))
    assert own.json()["items"][0]["mine"] is True


def test_shipping_sets_eta_pickup_does_not(client: TestClient) -> None:
    _s, seller_token, _b, buyer_token, sell_id = _paid_envio(client)
    shipped = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "en_viaje"},
        headers=_auth(seller_token),
    )
    assert shipped.status_code == 200
    assert shipped.json()["status"] == "en_viaje"
    eta = shipped.json()["eta_at"]
    assert eta
    parsed = datetime.fromisoformat(eta.replace("Z", "+00:00"))
    assert parsed > datetime.now().astimezone()

    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    paid = client.post(
        "/sells/checkout",
        json={
            "payment_method": "efectivo",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "fulfillment": "retiro",
                }
            ],
        },
        headers=_auth(buyer_token),
    )
    pickup_id = paid.json()["items"][0]["id"]
    ready = client.post(
        f"/sells/{pickup_id}/transition",
        json={"status": "esperando_retiro"},
        headers=_auth(seller_token),
    )
    assert ready.status_code == 200
    assert ready.json()["eta_at"] is None


def test_ws_invalid_auth_closes(client: TestClient) -> None:
    with client.websocket_connect("/ws", headers=WS_HEADERS) as ws:
        ws.send_json({"type": "auth", "token": "invalido"})
        try:
            ws.receive_json()
            raise AssertionError("expected close")
        except WebSocketDisconnect:
            pass


def test_message_reaches_watcher_without_notification(client: TestClient) -> None:
    _s, seller_token, _b, buyer_token, sell_id = _paid_envio(client)
    with client.websocket_connect("/ws", headers=WS_HEADERS) as ws:
        ws.send_json({"type": "auth", "token": buyer_token})
        ws.send_json({"type": "watch", "sell_id": sell_id})
        time.sleep(0.05)
        posted = client.post(
            f"/sells/{sell_id}/messages",
            json={"body": "sale mañana"},
            headers=_auth(seller_token),
        )
        assert posted.status_code == 201
        event = ws.receive_json()
        assert event["type"] == "message"
        assert event["message"]["body"] == "sale mañana"
    notes = client.get("/notifications", headers=_auth(buyer_token))
    assert notes.status_code == 200
    assert notes.json()["unread"] == 0
    assert notes.json()["total"] == 0


def test_message_notifies_when_not_watching(client: TestClient) -> None:
    _s, seller_token, _b, buyer_token, sell_id = _paid_envio(client)
    client.post("/notifications/read-all", headers=_auth(seller_token))
    posted = client.post(
        f"/sells/{sell_id}/messages",
        json={"body": "¿llegó?"},
        headers=_auth(buyer_token),
    )
    assert posted.status_code == 201
    notes = client.get("/notifications", headers=_auth(seller_token))
    assert notes.status_code == 200
    assert notes.json()["unread"] == 1
    item = notes.json()["items"][0]
    assert item["kind"] == "mensaje"
    assert item["sell_id"] == sell_id
    marked = client.post(
        f"/notifications/{item['id']}/read",
        headers=_auth(seller_token),
    )
    assert marked.status_code == 200
    assert marked.json()["read_at"]
    leftover = client.get(
        "/notifications",
        params={"unread": True},
        headers=_auth(seller_token),
    )
    assert leftover.json()["unread"] == 0


def test_status_notifies_buyer(client: TestClient) -> None:
    _s, seller_token, _b, buyer_token, sell_id = _paid_envio(client)
    shipped = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "en_viaje"},
        headers=_auth(seller_token),
    )
    assert shipped.status_code == 200
    notes = client.get("/notifications", headers=_auth(buyer_token))
    assert notes.json()["unread"] == 1
    assert notes.json()["items"][0]["kind"] == "estado"
    client.post("/notifications/read-all", headers=_auth(buyer_token))
    after = client.get("/notifications", headers=_auth(buyer_token))
    assert after.json()["unread"] == 0


def test_checkout_notifies_seller_not_buyer(client: TestClient) -> None:
    _s, seller_token, _b, buyer_token, sell_id = _paid_envio(client)
    seller_notes = client.get("/notifications", headers=_auth(seller_token))
    assert seller_notes.status_code == 200
    assert seller_notes.json()["unread"] == 1
    item = seller_notes.json()["items"][0]
    assert item["kind"] == "venta"
    assert item["sell_id"] == sell_id
    assert item["as_seller"] is True
    buyer_notes = client.get("/notifications", headers=_auth(buyer_token))
    assert buyer_notes.json()["unread"] == 0


def test_question_notifies_seller_when_not_watching(client: TestClient) -> None:
    _s, seller_token = _register(client)
    store_id, _ = _create_listed_store(client, seller_token)
    product = _create_listed_product(client, seller_token, store_id)
    _b, buyer_token = _register(client)
    product_id = product["id"]
    asked = client.post(
        f"/products/{product_id}/questions",
        json={"text": "Hay talle M?"},
        headers=_auth(buyer_token),
    )
    assert asked.status_code == 201
    notes = client.get("/notifications", headers=_auth(seller_token))
    assert notes.json()["unread"] == 1
    item = notes.json()["items"][0]
    assert item["kind"] == "pregunta"
    assert item["product_id"] == product_id
    assert item["sell_id"] is None


def test_question_reaches_product_watcher_without_notification(
    client: TestClient,
) -> None:
    _s, seller_token = _register(client)
    store_id, _ = _create_listed_store(client, seller_token)
    product = _create_listed_product(client, seller_token, store_id)
    _b, buyer_token = _register(client)
    product_id = product["id"]
    with client.websocket_connect("/ws", headers=WS_HEADERS) as ws:
        ws.send_json({"type": "auth", "token": seller_token})
        ws.send_json({"type": "watch", "product_id": product_id})
        time.sleep(0.05)
        asked = client.post(
            f"/products/{product_id}/questions",
            json={"text": "Hay talle M?"},
            headers=_auth(buyer_token),
        )
        assert asked.status_code == 201
        event = ws.receive_json()
        assert event["type"] == "question"
        assert event["product_id"] == product_id
        assert event["question"]["text"] == "Hay talle M?"
    notes = client.get("/notifications", headers=_auth(seller_token))
    assert notes.json()["unread"] == 0


def test_answer_notifies_asker_when_not_watching(client: TestClient) -> None:
    _s, seller_token = _register(client)
    store_id, _ = _create_listed_store(client, seller_token)
    product = _create_listed_product(client, seller_token, store_id)
    _b, buyer_token = _register(client)
    product_id = product["id"]
    asked = client.post(
        f"/products/{product_id}/questions",
        json={"text": "Hay talle M?"},
        headers=_auth(buyer_token),
    )
    assert asked.status_code == 201
    answered = client.post(
        f"/questions/{asked.json()['id']}/answers",
        json={"text": "Sí, hay M"},
        headers=_auth(seller_token),
    )
    assert answered.status_code == 200
    notes = client.get("/notifications", headers=_auth(buyer_token))
    assert notes.json()["unread"] == 1
    item = notes.json()["items"][0]
    assert item["kind"] == "respuesta"
    assert item["product_id"] == product_id
