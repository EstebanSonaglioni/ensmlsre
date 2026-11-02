from datetime import UTC, datetime, timedelta
from io import BytesIO

from app.core.db import get_session_factory
from app.models.product import ProductQuestion
from fastapi.testclient import TestClient
from tests.test_products import _auth, _create_store, _register

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
    b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _create_product(
    client: TestClient,
    token: str,
    store_id: int,
    name: str = "Remera",
    net_profit: str = "0",
) -> dict:
    response = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": name,
            "quantity": "3",
            "price": "199.50",
            "net_profit": net_profit,
            "category": "Ropa",
            "subcategory": "Remeras",
        },
        files={"image": ("remera.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _ask(
    client: TestClient, token: str, product_id: int, text: str = "Hay talle M?"
) -> dict:
    asked = client.post(
        f"/products/{product_id}/questions",
        json={"text": text},
        headers=_auth(token),
    )
    assert asked.status_code == 201, asked.text
    return asked.json()


def _age_question(question_id: int, hours: float) -> None:
    session = get_session_factory()()
    question = session.get(ProductQuestion, question_id)
    assert question is not None
    question.created_at = datetime.now(UTC) - timedelta(hours=hours)
    session.commit()
    session.close()


def test_pending_questions_ordered_by_score(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    high = _create_product(
        client, seller_token, store_id, name="Cara", net_profit="10.00"
    )
    low = _create_product(
        client, seller_token, store_id, name="Barata", net_profit="0"
    )
    _buyer, buyer_token = _register(client)
    old_high = _ask(client, buyer_token, high["id"], "La cara?")
    recent_low = _ask(client, buyer_token, low["id"], "La barata?")
    _age_question(old_high["id"], 5)
    _age_question(recent_low["id"], 1)

    listed = client.get("/questions", headers=_auth(seller_token))
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 2
    assert [item["text"] for item in body["items"]] == ["La cara?", "La barata?"]
    first = body["items"][0]
    assert first["wait_hours"] == "5.00"
    assert first["net_profit"] == "10.00"
    assert first["score"] == "15.00"
    second = body["items"][1]
    assert second["wait_hours"] == "1.00"
    assert second["score"] == "1.00"


def test_answered_question_excluded_from_pending_and_wait_is_zero(
    client: TestClient,
) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(
        client, seller_token, store_id, name="Remera", net_profit="8.50"
    )
    _buyer, buyer_token = _register(client)
    asked = _ask(client, buyer_token, product["id"])
    _age_question(asked["id"], 4)
    answered = client.post(
        f"/questions/{asked['id']}/answers",
        json={"text": "Sí"},
        headers=_auth(seller_token),
    )
    assert answered.status_code == 200

    pending = client.get("/questions", headers=_auth(seller_token))
    assert pending.status_code == 200
    assert pending.json()["total"] == 0
    assert pending.json()["items"] == []

    all_rows = client.get(
        "/questions",
        params={"status": "answered"},
        headers=_auth(seller_token),
    )
    assert all_rows.status_code == 200
    item = all_rows.json()["items"][0]
    assert item["wait_hours"] == "0.00"
    assert item["net_profit"] == "8.50"
    assert item["score"] == "8.50"
    assert item["answer"] == "Sí"


def test_buyer_cannot_list_seller_questions(client: TestClient) -> None:
    _buyer, buyer_token = _register(client)
    response = client.get("/questions", headers=_auth(buyer_token))
    assert response.status_code == 403
    assert response.json() == {"detail": "No se pudo completar la solicitud"}


def test_other_store_question_is_hidden(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    _create_product(client, seller_token, store_id)
    _other, other_token = _register(client)
    other_store, _ = _create_store(client, other_token)
    other_product = _create_product(client, other_token, other_store, name="Ajena")
    _buyer, buyer_token = _register(client)
    _ask(client, buyer_token, other_product["id"], "De la otra tienda")

    listed = client.get("/questions", headers=_auth(seller_token))
    assert listed.status_code == 200
    assert listed.json()["total"] == 0


def test_invalid_sort_returns_generic_error(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    _create_store(client, seller_token)
    response = client.get(
        "/questions",
        params={"sort": "popularidad"},
        headers=_auth(seller_token),
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}


def test_question_with_html_is_rejected(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)
    asked = client.post(
        f"/products/{product['id']}/questions",
        json={"text": "<script>alert(1)</script> hay stock?"},
        headers=_auth(buyer_token),
    )
    assert asked.status_code == 422
    assert asked.json() == {"detail": "Los datos enviados no son válidos"}
    listed = client.get("/questions", headers=_auth(seller_token))
    assert listed.status_code == 200
    assert listed.json()["total"] == 0
