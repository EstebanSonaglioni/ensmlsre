import uuid
from decimal import Decimal
from io import BytesIO

from fastapi.testclient import TestClient

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
    b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _register(client: TestClient) -> tuple[str, str]:
    email = f"ana.sell.{uuid.uuid4().hex}@example.com"
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "secreto-valido"},
    )
    assert registered.status_code == 201
    return email, registered.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_store(client: TestClient, token: str) -> int:
    name = f"Tienda sell {uuid.uuid4().hex[:8]}"
    created = client.post("/stores", json={"name": name}, headers=_auth(token))
    assert created.status_code == 201
    return created.json()["id"]


def _create_product(
    client: TestClient,
    token: str,
    store_id: int,
    *,
    name: str = "Remera",
    quantity: str = "3",
    price: str = "199.50",
    ships: str = "true",
    pickup: str = "true",
) -> dict:
    response = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": name,
            "quantity": quantity,
            "price": price,
            "category": "Ropa",
            "subcategory": "Remeras",
            "ships": ships,
            "pickup": pickup,
        },
        files={"image": ("remera.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_buy_now_credits_seller_and_drops_stock(client: TestClient) -> None:
    seller_email, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer_email, buyer_token = _register(client)

    paid = client.post(
        "/sells/checkout",
        json={
            "payment_method": "tarjeta",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 2,
                    "fulfillment": "envio",
                }
            ],
        },
        headers=_auth(buyer_token),
    )
    assert paid.status_code == 200, paid.text
    item = paid.json()["items"][0]
    assert item["status"] == "en_curso"
    assert item["quantity"] == 2
    assert item["subtotal"] == "399.00"
    assert item["checkout_id"]

    listed = client.get(f"/products/{product['id']}", headers=_auth(buyer_token))
    assert listed.json()["quantity"] == 1

    client.get("/auth/me", headers=_auth(seller_token))
    # cookie session for seller may be overwritten; use DB via login token on /stores
    # seller JWT still valid for stores; balance is on /auth/me cookie of last user.
    seller_me = client.post(
        "/auth/login",
        json={"email": seller_email, "password": "secreto-valido"},
    )
    assert Decimal(seller_me.json()["balance"]) == Decimal("399.00")

    buyer_me = client.post(
        "/auth/login",
        json={"email": _buyer_email, "password": "secreto-valido"},
    )
    assert Decimal(buyer_me.json()["balance"]) == Decimal("0")


def test_cart_two_sellers_split_credit(client: TestClient) -> None:
    _s1, t1 = _register(client)
    store1 = _create_store(client, t1)
    p1 = _create_product(client, t1, store1, price="10.00", quantity="5")
    s2, t2 = _register(client)
    store2 = _create_store(client, t2)
    p2 = _create_product(client, t2, store2, price="20.00", quantity="5")
    _buyer, buyer_token = _register(client)

    a = client.post(
        "/sells",
        json={"product_id": p1["id"], "quantity": 1, "fulfillment": "retiro"},
        headers=_auth(buyer_token),
    )
    b = client.post(
        "/sells",
        json={"product_id": p2["id"], "quantity": 2, "fulfillment": "envio"},
        headers=_auth(buyer_token),
    )
    assert a.status_code == 201
    assert b.status_code == 201

    paid = client.post(
        "/sells/checkout",
        json={"payment_method": "efectivo"},
        headers=_auth(buyer_token),
    )
    assert paid.status_code == 200
    items = paid.json()["items"]
    assert len(items) == 2
    assert items[0]["checkout_id"] == items[1]["checkout_id"]
    assert {item["status"] for item in items} == {"en_curso"}

    one = client.post("/auth/login", json={"email": _s1, "password": "secreto-valido"})
    two = client.post("/auth/login", json={"email": s2, "password": "secreto-valido"})
    assert Decimal(one.json()["balance"]) == Decimal("10.00")
    assert Decimal(two.json()["balance"]) == Decimal("40.00")


def test_shipping_and_pickup_state_machine(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)
    paid = client.post(
        "/sells/checkout",
        json={
            "payment_method": "transferencia",
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
    sell_id = paid.json()["items"][0]["id"]
    illegal = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "esperando_retiro"},
        headers=_auth(seller_token),
    )
    assert illegal.status_code == 422
    shipped = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "en_viaje"},
        headers=_auth(seller_token),
    )
    assert shipped.status_code == 200
    assert shipped.json()["status"] == "en_viaje"
    done = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "completada"},
        headers=_auth(seller_token),
    )
    assert done.json()["status"] == "completada"


def test_pickup_flow_and_refund(client: TestClient) -> None:
    seller_email, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id, quantity="4")
    _buyer, buyer_token = _register(client)
    paid = client.post(
        "/sells/checkout",
        json={
            "payment_method": "tarjeta",
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
    sell_id = paid.json()["items"][0]["id"]
    ready = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "esperando_retiro"},
        headers=_auth(seller_token),
    )
    assert ready.json()["status"] == "esperando_retiro"
    done = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "completada"},
        headers=_auth(seller_token),
    )
    assert done.json()["status"] == "completada"
    refund = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "reembolsada"},
        headers=_auth(seller_token),
    )
    assert refund.json()["status"] == "reembolsada"
    listed = client.get(f"/products/{product['id']}", headers=_auth(seller_token))
    assert listed.json()["quantity"] == 4
    seller = client.post(
        "/auth/login",
        json={"email": seller_email, "password": "secreto-valido"},
    )
    assert Decimal(seller.json()["balance"]) == Decimal("0.00")


def test_cannot_buy_more_than_stock(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id, quantity="1")
    _buyer, buyer_token = _register(client)
    response = client.post(
        "/sells",
        json={"product_id": product["id"], "quantity": 2, "fulfillment": "envio"},
        headers=_auth(buyer_token),
    )
    assert response.status_code == 409


def test_cannot_buy_own_product(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    response = client.post(
        "/sells",
        json={"product_id": product["id"], "quantity": 1, "fulfillment": "envio"},
        headers=_auth(seller_token),
    )
    assert response.status_code == 403


def test_fulfillment_not_offered(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(
        client, seller_token, store_id, ships="false", pickup="true"
    )
    _buyer, buyer_token = _register(client)
    response = client.post(
        "/sells",
        json={"product_id": product["id"], "quantity": 1, "fulfillment": "envio"},
        headers=_auth(buyer_token),
    )
    assert response.status_code == 422


def test_empty_checkout_is_invalid(client: TestClient) -> None:
    _buyer, buyer_token = _register(client)
    response = client.post(
        "/sells/checkout",
        json={"payment_method": "tarjeta"},
        headers=_auth(buyer_token),
    )
    assert response.status_code == 422


def test_invalid_payment_method(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)
    response = client.post(
        "/sells/checkout",
        json={
            "payment_method": "crypto",
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
    assert response.status_code == 422


def test_cancel_in_progress_restores_stock(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id, quantity="3")
    _buyer, buyer_token = _register(client)
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
    sell_id = paid.json()["items"][0]["id"]
    cancelled = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "cancelada"},
        headers=_auth(buyer_token),
    )
    assert cancelled.json()["status"] == "cancelada"
    listed = client.get(f"/products/{product['id']}", headers=_auth(buyer_token))
    assert listed.json()["quantity"] == 3


def test_sold_out_purchase_pauses_product(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id, quantity="2")
    _buyer, buyer_token = _register(client)

    paid = client.post(
        "/sells/checkout",
        json={
            "payment_method": "tarjeta",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 2,
                    "fulfillment": "envio",
                }
            ],
        },
        headers=_auth(buyer_token),
    )
    assert paid.status_code == 200, paid.text

    hidden = client.get(f"/products/{product['id']}", headers=_auth(buyer_token))
    assert hidden.status_code == 404

    own = client.get(f"/products/{product['id']}", headers=_auth(seller_token))
    assert own.status_code == 200
    assert own.json()["quantity"] == 0
    assert own.json()["paused"] is True


def test_both_delivery_flags_false_rejected(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    response = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": "Remera",
            "quantity": "1",
            "price": "10",
            "category": "Ropa",
            "subcategory": "Remeras",
            "ships": "false",
            "pickup": "false",
        },
        files={"image": ("remera.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(seller_token),
    )
    assert response.status_code == 422


def test_list_sells_filters_by_date_range(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)
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
    assert paid.status_code == 200
    listed = client.get(
        "/sells",
        params={"as_seller": True, "from": "2000-01-01"},
        headers=_auth(seller_token),
    )
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    empty = client.get(
        "/sells",
        params={"as_seller": True, "from": "2099-01-01"},
        headers=_auth(seller_token),
    )
    assert empty.status_code == 200
    assert empty.json()["total"] == 0
    inverted = client.get(
        "/sells",
        params={"as_seller": True, "from": "2026-12-01", "to": "2026-01-01"},
        headers=_auth(seller_token),
    )
    assert inverted.status_code == 422
    assert inverted.json() == {"detail": "Los datos enviados no son válidos"}
    invalid = client.get(
        "/sells",
        params={"as_seller": True, "from": "ayer"},
        headers=_auth(seller_token),
    )
    assert invalid.status_code == 422
    assert invalid.json() == {"detail": "Los datos enviados no son válidos"}


def test_list_sells_includes_created_at_and_sorts(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    cheap = _create_product(
        client, seller_token, store_id, name="Barata", price="10.00"
    )
    pricey = _create_product(
        client, seller_token, store_id, name="Cara", price="80.00"
    )
    _buyer, buyer_token = _register(client)
    for product in (cheap, pricey):
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
        assert paid.status_code == 200

    listed = client.get(
        "/sells",
        params={"as_seller": True, "sort": "subtotal", "order": "asc"},
        headers=_auth(seller_token),
    )
    assert listed.status_code == 200
    body = listed.json()
    amounts = [item["subtotal"] for item in body["items"]]
    assert amounts == sorted(amounts)
    assert body["items"][0]["created_at"]
    names = client.get(
        "/sells",
        params={"as_seller": True, "sort": "product_name", "order": "asc"},
        headers=_auth(seller_token),
    )
    assert names.status_code == 200
    assert [item["product_name"] for item in names.json()["items"]] == [
        "Barata",
        "Cara",
    ]


def test_list_sells_rejects_invalid_sort(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    _create_store(client, seller_token)
    response = client.get(
        "/sells",
        params={"as_seller": True, "sort": "secreto"},
        headers=_auth(seller_token),
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}


def test_list_sells_filters_by_buyer_q(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    buyer_a, token_a = _register(client)
    buyer_b, token_b = _register(client)
    paid_a = client.post(
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
        headers=_auth(token_a),
    )
    paid_b = client.post(
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
        headers=_auth(token_b),
    )
    assert paid_a.status_code == 200
    assert paid_b.status_code == 200
    only_a = client.get(
        "/sells",
        params={"as_seller": True, "q": buyer_a},
        headers=_auth(seller_token),
    )
    assert only_a.status_code == 200
    emails = {item["buyer_email"] for item in only_a.json()["items"]}
    assert emails == {buyer_a}
    _other, seller2_token = _register(client)
    _create_store(client, seller2_token)
    hidden = client.get(
        "/sells",
        params={"as_seller": True, "q": buyer_a},
        headers=_auth(seller2_token),
    )
    assert hidden.status_code == 200
    assert hidden.json()["total"] == 0
    too_long = client.get(
        "/sells",
        params={"as_seller": True, "q": "x" * 101},
        headers=_auth(seller_token),
    )
    assert too_long.status_code == 422
