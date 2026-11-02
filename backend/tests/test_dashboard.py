import uuid
from datetime import UTC, datetime, timedelta
from io import BytesIO

from app.core.db import get_session_factory
from app.models.sell import Sell
from fastapi.testclient import TestClient

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
    b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _register(client: TestClient) -> tuple[str, str]:
    email = f"ana.dash.{uuid.uuid4().hex}@example.com"
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "secreto-valido"},
    )
    assert registered.status_code == 201
    return email, registered.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_store(client: TestClient, token: str) -> tuple[int, str]:
    name = f"Tienda dash {uuid.uuid4().hex[:8]}"
    created = client.post("/stores", json={"name": name}, headers=_auth(token))
    assert created.status_code == 201
    return created.json()["id"], name


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
            "quantity": "8",
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


def _checkout(
    client: TestClient,
    token: str,
    product_id: int,
    quantity: int = 1,
    fulfillment: str = "envio",
) -> int:
    paid = client.post(
        "/sells/checkout",
        json={
            "payment_method": "tarjeta",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "fulfillment": fulfillment,
                }
            ],
        },
        headers=_auth(token),
    )
    assert paid.status_code == 200, paid.text
    return paid.json()["items"][0]["id"]


def _complete_envio(client: TestClient, token: str, sell_id: int) -> None:
    shipped = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "en_viaje"},
        headers=_auth(token),
    )
    assert shipped.status_code == 200
    done = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "completada"},
        headers=_auth(token),
    )
    assert done.status_code == 200


def test_dashboard_counts_completed_sale(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id, name="Remera dash")
    _buyer, buyer_token = _register(client)
    sell_id = _checkout(client, buyer_token, product["id"], quantity=2)
    _complete_envio(client, seller_token, sell_id)

    dashboard = client.get("/dashboard", headers=_auth(seller_token))
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["days"] == 30
    assert body["sales_count"] == 1
    assert body["cancelled_count"] == 0
    assert body["total_amount"] == "399.00"
    assert body["units_sold"] == 2
    assert body["average_ticket"] == "399.00"
    assert body["top_products"][0]["name"] == "Remera dash"
    assert body["top_products"][0]["units"] == 2
    assert body["sellers"][0]["sales_count"] == 1


def test_dashboard_hides_other_seller_from_non_admin(client: TestClient) -> None:
    _admin, admin_token = _register(client)
    store_id, store_name = _create_store(client, admin_token)
    invitee_email, invitee_token = _register(client)
    client.post(
        "/stores/invitations",
        json={"email": invitee_email, "store": store_name},
        headers=_auth(admin_token),
    )
    accepted = client.post(
        "/stores/invitations/accept",
        json={"store": store_name},
        headers=_auth(invitee_token),
    )
    assert accepted.status_code == 200
    own = _create_product(client, invitee_token, store_id, name="Gorra dash")
    admin_product = _create_product(
        client, admin_token, store_id, name="Admin dash"
    )
    _buyer, buyer_token = _register(client)
    own_sell = _checkout(client, buyer_token, own["id"])
    admin_sell = _checkout(client, buyer_token, admin_product["id"])
    _complete_envio(client, invitee_token, own_sell)
    _complete_envio(client, admin_token, admin_sell)

    as_seller = client.get("/dashboard", headers=_auth(invitee_token))
    assert as_seller.status_code == 200
    seller_body = as_seller.json()
    assert seller_body["sales_count"] == 1
    assert seller_body["top_products"][0]["name"] == "Gorra dash"
    assert seller_body["sellers"] == []

    as_admin = client.get("/dashboard", headers=_auth(admin_token))
    assert as_admin.status_code == 200
    admin_body = as_admin.json()
    assert admin_body["sales_count"] == 2
    names = {item["name"] for item in admin_body["top_products"]}
    assert names == {"Gorra dash", "Admin dash"}
    emails = {item["email"] for item in admin_body["sellers"]}
    assert invitee_email in emails


def test_dashboard_ignores_cart_open_and_cancelled(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    cart_product = _create_product(client, seller_token, store_id, name="Cart")
    open_product = _create_product(client, seller_token, store_id, name="Open")
    cancel_product = _create_product(client, seller_token, store_id, name="Cancel")
    _buyer, buyer_token = _register(client)
    cart = client.post(
        "/sells",
        json={
            "product_id": cart_product["id"],
            "quantity": 1,
            "fulfillment": "envio",
        },
        headers=_auth(buyer_token),
    )
    assert cart.status_code == 201
    open_id = _checkout(client, buyer_token, open_product["id"])
    cancelled = _checkout(client, buyer_token, cancel_product["id"])
    client.post(
        f"/sells/{cancelled}/transition",
        json={"status": "cancelada"},
        headers=_auth(buyer_token),
    )

    dashboard = client.get("/dashboard", headers=_auth(seller_token))
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["sales_count"] == 0
    assert body["total_amount"] == "0.00"
    assert body["open_orders"] == 1
    assert body["cancelled_count"] == 1
    assert open_id > 0


def test_dashboard_refunds_are_not_sales(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)
    sell_id = _checkout(client, buyer_token, product["id"], fulfillment="retiro")
    ready = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "esperando_retiro"},
        headers=_auth(seller_token),
    )
    assert ready.status_code == 200
    done = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "completada"},
        headers=_auth(seller_token),
    )
    assert done.status_code == 200
    refund = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "reembolsada"},
        headers=_auth(seller_token),
    )
    assert refund.status_code == 200

    dashboard = client.get("/dashboard", headers=_auth(seller_token))
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["sales_count"] == 0
    assert body["refunded_count"] == 1
    assert body["refunded_amount"] == "199.50"


def test_dashboard_excludes_completed_outside_seven_days(
    client: TestClient,
) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)
    sell_id = _checkout(client, buyer_token, product["id"])
    _complete_envio(client, seller_token, sell_id)

    session = get_session_factory()()
    sell = session.get(Sell, sell_id)
    assert sell is not None
    sell.updated_at = datetime.now(UTC) - timedelta(days=10)
    session.commit()
    session.close()

    week = client.get("/dashboard", params={"days": 7}, headers=_auth(seller_token))
    assert week.status_code == 200
    assert week.json()["sales_count"] == 0
    month = client.get("/dashboard", params={"days": 30}, headers=_auth(seller_token))
    assert month.status_code == 200
    assert month.json()["sales_count"] == 1


def test_dashboard_excludes_cancelled_outside_seven_days(
    client: TestClient,
) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)
    sell_id = _checkout(client, buyer_token, product["id"])
    cancelled = client.post(
        f"/sells/{sell_id}/transition",
        json={"status": "cancelada"},
        headers=_auth(buyer_token),
    )
    assert cancelled.status_code == 200

    session = get_session_factory()()
    sell = session.get(Sell, sell_id)
    assert sell is not None
    sell.updated_at = datetime.now(UTC) - timedelta(days=10)
    session.commit()
    session.close()

    week = client.get("/dashboard", params={"days": 7}, headers=_auth(seller_token))
    assert week.status_code == 200
    assert week.json()["cancelled_count"] == 0
    month = client.get("/dashboard", params={"days": 30}, headers=_auth(seller_token))
    assert month.status_code == 200
    assert month.json()["cancelled_count"] == 1


def test_dashboard_buyer_is_forbidden(client: TestClient) -> None:
    _buyer, buyer_token = _register(client)
    response = client.get("/dashboard", headers=_auth(buyer_token))
    assert response.status_code == 403
    assert response.json() == {"detail": "No se pudo completar la solicitud"}


def test_dashboard_sums_net_profit_from_completed_units(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    paid = _create_product(
        client, seller_token, store_id, name="Con ganancia", net_profit="10.00"
    )
    zero = _create_product(
        client, seller_token, store_id, name="Sin ganancia", net_profit="0"
    )
    _buyer, buyer_token = _register(client)
    sell_paid = _checkout(client, buyer_token, paid["id"], quantity=2)
    sell_zero = _checkout(client, buyer_token, zero["id"], quantity=3)
    _complete_envio(client, seller_token, sell_paid)
    _complete_envio(client, seller_token, sell_zero)

    dashboard = client.get("/dashboard", headers=_auth(seller_token))
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["net_profit_total"] == "20.00"
    by_name = {item["name"]: item for item in body["top_products"]}
    assert by_name["Con ganancia"]["net_profit"] == "20.00"
    assert by_name["Sin ganancia"]["net_profit"] == "0.00"
