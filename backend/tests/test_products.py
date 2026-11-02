import uuid
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
    b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _register(client: TestClient) -> tuple[str, str]:
    email = f"ana.prod.{uuid.uuid4().hex}@example.com"
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "secreto-valido"},
    )
    assert registered.status_code == 201
    return email, registered.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_store(client: TestClient, token: str) -> tuple[int, str]:
    name = f"Tienda prod {uuid.uuid4().hex[:8]}"
    created = client.post("/stores", json={"name": name}, headers=_auth(token))
    assert created.status_code == 201
    return created.json()["id"], name


def _create_product(
    client: TestClient,
    token: str,
    store_id: int,
    name: str = "Remera",
) -> dict:
    response = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": name,
            "quantity": "3",
            "price": "199.50",
            "category": "Ropa",
            "subcategory": "Remeras",
        },
        files={"image": ("remera.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_pytest_writes_product_images_outside_app_dir() -> None:
    from app.core.config import get_settings

    stored = Path(get_settings().PRODUCT_IMAGES_DIR).resolve()
    assert stored == (Path(__file__).resolve().parent / "_test_images").resolve()


def test_seller_publishes_product_with_image(client: TestClient) -> None:
    _email, token = _register(client)
    store_id, store_name = _create_store(client, token)

    body = _create_product(client, token, store_id)

    assert body["name"] == "Remera"
    assert body["quantity"] == 3
    assert body["price"] == "199.50"
    assert body["net_profit"] == "0.00"
    assert body["category"] == "Ropa"
    assert body["subcategory"] == "Remeras"
    assert body["paused"] is False
    assert body["store_id"] == store_id
    assert body["store_name"] == store_name
    assert body["id"] > 0

    image = client.get(f"/products/{body['id']}/image", headers=_auth(token))
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content.startswith(b"\x89PNG")


def test_buyer_can_see_catalog_product_image(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)
    image = client.get(f"/products/{product['id']}/image", headers=_auth(buyer_token))
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content.startswith(b"\x89PNG")


def test_create_product_without_image_returns_generic_error(
    client: TestClient,
) -> None:
    _email, token = _register(client)
    store_id, _ = _create_store(client, token)
    response = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": "Remera",
            "quantity": "3",
            "price": "199.50",
            "category": "Ropa",
            "subcategory": "Remeras",
        },
        headers=_auth(token),
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}


def test_create_product_invalid_data_returns_generic_error(
    client: TestClient,
) -> None:
    _email, token = _register(client)
    store_id, _ = _create_store(client, token)
    response = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": "X",
            "quantity": "-1",
            "price": "10",
            "category": "A",
            "subcategory": "B",
        },
        files={"image": ("remera.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}


def test_non_member_cannot_publish(client: TestClient) -> None:
    _admin, admin_token = _register(client)
    store_id, _ = _create_store(client, admin_token)
    _other, other_token = _register(client)
    response = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": "X",
            "quantity": "1",
            "price": "10",
            "category": "A",
            "subcategory": "B",
        },
        files={"image": ("remera.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(other_token),
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "No se pudo completar la solicitud"}


def test_invitee_can_publish_after_accepting(client: TestClient) -> None:
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
    body = _create_product(client, invitee_token, store_id, name="Gorra")
    assert body["name"] == "Gorra"
    assert "seller_email" not in body
    assert body["store_name"] == store_name


def test_owner_pauses_and_other_buyer_does_not_see_it(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    paused = client.post(
        f"/products/{product['id']}/pause",
        headers=_auth(seller_token),
    )
    assert paused.status_code == 200
    assert paused.json()["paused"] is True

    _buyer, buyer_token = _register(client)
    listed = client.get("/products", headers=_auth(buyer_token))
    assert listed.status_code == 200
    assert all(item["id"] != product["id"] for item in listed.json()["items"])

    hidden = client.get(f"/products/{product['id']}", headers=_auth(buyer_token))
    assert hidden.status_code == 404

    own_catalog = client.get("/products", headers=_auth(seller_token))
    assert all(item["id"] != product["id"] for item in own_catalog.json()["items"])

    own = client.get("/products/mine", headers=_auth(seller_token))
    assert any(
        item["id"] == product["id"] and item["paused"]
        for item in own.json()["items"]
    )


def test_admin_can_pause_another_seller_listing(client: TestClient) -> None:
    _admin, admin_token = _register(client)
    store_id, store_name = _create_store(client, admin_token)
    invitee_email, invitee_token = _register(client)
    client.post(
        "/stores/invitations",
        json={"email": invitee_email, "store": store_name},
        headers=_auth(admin_token),
    )
    client.post(
        "/stores/invitations/accept",
        json={"store": store_name},
        headers=_auth(invitee_token),
    )
    product = _create_product(client, invitee_token, store_id)
    paused = client.post(
        f"/products/{product['id']}/pause",
        headers=_auth(admin_token),
    )
    assert paused.status_code == 200
    assert paused.json()["paused"] is True
    resumed = client.post(
        f"/products/{product['id']}/resume",
        headers=_auth(admin_token),
    )
    assert resumed.status_code == 200
    assert resumed.json()["paused"] is False


def test_stranger_cannot_pause(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _other, other_token = _register(client)
    response = client.post(
        f"/products/{product['id']}/pause",
        headers=_auth(other_token),
    )
    assert response.status_code == 403


def test_ask_and_answer_on_listing(client: TestClient) -> None:
    seller_email, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    asker_email, asker_token = _register(client)

    asked = client.post(
        f"/products/{product['id']}/questions",
        json={"text": "Hay talle M?"},
        headers=_auth(asker_token),
    )
    assert asked.status_code == 201
    question_id = asked.json()["id"]
    assert asked.json()["answer"] is None
    assert asked.json()["asker_label"] == "Comprador"
    assert not asked.json().get("asker_email")

    forbidden = client.post(
        f"/questions/{question_id}/answers",
        json={"text": "No soy el vendedor"},
        headers=_auth(asker_token),
    )
    assert forbidden.status_code == 403

    answered = client.post(
        f"/questions/{question_id}/answers",
        json={"text": "Sí, hay M"},
        headers=_auth(seller_token),
    )
    assert answered.status_code == 200
    assert answered.json()["answer"] == "Sí, hay M"

    detail = client.get(f"/products/{product['id']}", headers=_auth(asker_token))
    assert detail.status_code == 200
    assert detail.json()["questions"][0]["text"] == "Hay talle M?"
    assert detail.json()["questions"][0]["answer"] == "Sí, hay M"
    assert not detail.json().get("net_profit")
    assert "seller_email" not in detail.json()
    assert not detail.json()["questions"][0].get("asker_email")
    assert seller_email
    managed = client.get(f"/products/{product['id']}", headers=_auth(seller_token))
    assert managed.json()["net_profit"] == "0.00"
    assert managed.json()["questions"][0]["asker_email"] == asker_email


def test_seller_cannot_ask_on_own_product(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    response = client.post(
        f"/products/{product['id']}/questions",
        json={"text": "Hay talle M?"},
        headers=_auth(seller_token),
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "No se pudo completar la solicitud"}


def test_store_admin_cannot_ask_on_store_product(client: TestClient) -> None:
    _admin, admin_token = _register(client)
    store_id, store_name = _create_store(client, admin_token)
    invitee_email, invitee_token = _register(client)
    client.post(
        "/stores/invitations",
        json={"email": invitee_email, "store": store_name},
        headers=_auth(admin_token),
    )
    client.post(
        "/stores/invitations/accept",
        json={"store": store_name},
        headers=_auth(invitee_token),
    )
    product = _create_product(client, invitee_token, store_id)
    response = client.post(
        f"/products/{product['id']}/questions",
        json={"text": "Hay talle M?"},
        headers=_auth(admin_token),
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "No se pudo completar la solicitud"}


def test_second_answer_returns_generic_error(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)
    asked = client.post(
        f"/products/{product['id']}/questions",
        json={"text": "Color?"},
        headers=_auth(buyer_token),
    )
    question_id = asked.json()["id"]
    first = client.post(
        f"/questions/{question_id}/answers",
        json={"text": "Rojo"},
        headers=_auth(seller_token),
    )
    assert first.status_code == 200
    second = client.post(
        f"/questions/{question_id}/answers",
        json={"text": "Azul"},
        headers=_auth(seller_token),
    )
    assert second.status_code == 409
    assert second.json() == {"detail": "No se pudo responder la pregunta"}


def test_oversized_product_body_is_rejected(client: TestClient) -> None:
    _email, token = _register(client)
    store_id, _ = _create_store(client, token)
    response = client.post(
        f"/stores/{store_id}/products",
        headers={**_auth(token), "Content-Length": str(1_000_001)},
        content=b"x",
    )
    assert response.status_code == 413
    assert response.json() == {
        "detail": "El cuerpo de la solicitud es demasiado grande"
    }


def _patch_fields(**overrides: str) -> dict[str, str]:
    fields = {
        "name": "Campera",
        "quantity": "8",
        "price": "450.00",
        "category": "Abrigos",
        "subcategory": "Camperas",
    }
    fields.update(overrides)
    return fields


def test_seller_updates_product_fields(client: TestClient) -> None:
    _email, token = _register(client)
    store_id, store_name = _create_store(client, token)
    product = _create_product(client, token, store_id)

    response = client.patch(
        f"/products/{product['id']}",
        data=_patch_fields(),
        headers=_auth(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Campera"
    assert body["quantity"] == 8
    assert body["price"] == "450.00"
    assert body["category"] == "Abrigos"
    assert body["subcategory"] == "Camperas"
    assert body["store_id"] == store_id
    assert body["store_name"] == store_name
    assert "seller_email" not in body
    assert "seller_email" not in product


def test_seller_updates_product_image(client: TestClient) -> None:
    _email, token = _register(client)
    store_id, _ = _create_store(client, token)
    product = _create_product(client, token, store_id)
    tiny_gif = (
        b"GIF89a\x01\x00\x01\x00\x00\x00\x00,\x00\x00\x00\x00"
        b"\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )

    response = client.patch(
        f"/products/{product['id']}",
        data=_patch_fields(name="Remera"),
        files={"image": ("nueva.gif", BytesIO(tiny_gif), "image/gif")},
        headers=_auth(token),
    )

    assert response.status_code == 200
    image = client.get(f"/products/{product['id']}/image", headers=_auth(token))
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/gif"
    assert image.content.startswith(b"GIF89a")


def test_buyer_cannot_update_product(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)

    response = client.patch(
        f"/products/{product['id']}",
        data=_patch_fields(),
        headers=_auth(buyer_token),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "No se pudo completar la solicitud"}
    listed = client.get(f"/products/{product['id']}", headers=_auth(seller_token))
    assert listed.json()["name"] == "Remera"


def test_update_invalid_data_does_not_persist(client: TestClient) -> None:
    _email, token = _register(client)
    store_id, _ = _create_store(client, token)
    product = _create_product(client, token, store_id)

    response = client.patch(
        f"/products/{product['id']}",
        data=_patch_fields(quantity="-2"),
        headers=_auth(token),
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}
    listed = client.get(f"/products/{product['id']}", headers=_auth(token))
    assert listed.json()["quantity"] == 3


def test_paused_product_update_hidden_from_buyer(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    client.post(f"/products/{product['id']}/pause", headers=_auth(seller_token))
    _buyer, buyer_token = _register(client)

    response = client.patch(
        f"/products/{product['id']}",
        data=_patch_fields(),
        headers=_auth(buyer_token),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "No se pudo completar la solicitud"}


def test_detail_includes_can_manage_for_seller_not_buyer(
    client: TestClient,
) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)

    own = client.get(f"/products/{product['id']}", headers=_auth(seller_token))
    other = client.get(f"/products/{product['id']}", headers=_auth(buyer_token))

    assert own.status_code == 200
    assert own.json()["can_manage"] is True
    assert other.status_code == 200
    assert other.json()["can_manage"] is False


def test_seller_deletes_product(client: TestClient) -> None:
    _email, token = _register(client)
    store_id, _ = _create_store(client, token)
    product = _create_product(client, token, store_id)
    _buyer, buyer_token = _register(client)
    asked = client.post(
        f"/products/{product['id']}/questions",
        json={"text": "Hay stock?"},
        headers=_auth(buyer_token),
    )
    assert asked.status_code == 201

    response = client.delete(
        f"/products/{product['id']}",
        headers=_auth(token),
    )

    assert response.status_code == 204
    missing = client.get(f"/products/{product['id']}", headers=_auth(token))
    assert missing.status_code == 404


def test_buyer_cannot_delete_product(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    _buyer, buyer_token = _register(client)

    response = client.delete(
        f"/products/{product['id']}",
        headers=_auth(buyer_token),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "No se pudo completar la solicitud"}
    still = client.get(f"/products/{product['id']}", headers=_auth(seller_token))
    assert still.status_code == 200


def test_paused_product_delete_hidden_from_buyer(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id)
    client.post(f"/products/{product['id']}/pause", headers=_auth(seller_token))
    _buyer, buyer_token = _register(client)

    response = client.delete(
        f"/products/{product['id']}",
        headers=_auth(buyer_token),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "No se pudo completar la solicitud"}


def test_catalog_shows_other_stores_and_mine_does_not(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    product = _create_product(client, seller_token, store_id, name="Ajena")

    _buyer, buyer_token = _register(client)
    catalog = client.get("/products", headers=_auth(buyer_token))
    assert catalog.status_code == 200
    assert any(item["id"] == product["id"] for item in catalog.json()["items"])

    mine = client.get("/products/mine", headers=_auth(buyer_token))
    assert mine.status_code == 200
    assert all(item["id"] != product["id"] for item in mine.json()["items"])


def test_mine_includes_store_listings_and_paused(client: TestClient) -> None:
    _admin, admin_token = _register(client)
    store_id, _ = _create_store(client, admin_token)
    product = _create_product(client, admin_token, store_id)
    client.post(f"/products/{product['id']}/pause", headers=_auth(admin_token))

    mine = client.get("/products/mine", headers=_auth(admin_token))
    assert mine.status_code == 200
    assert any(
        item["id"] == product["id"] and item["paused"]
        for item in mine.json()["items"]
    )


def test_catalog_search_filters_by_name(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    shirt = _create_product(client, seller_token, store_id, name="Remera")
    pants = _create_product(client, seller_token, store_id, name="Pantalón")

    _buyer, buyer_token = _register(client)
    listed = client.get("/products", params={"q": "ReMe"}, headers=_auth(buyer_token))
    assert listed.status_code == 200
    ids = [item["id"] for item in listed.json()["items"]]
    assert shirt["id"] in ids
    assert pants["id"] not in ids
    assert all("reme" in item["name"].casefold() for item in listed.json()["items"])


def test_catalog_search_empty_when_name_does_not_match(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    _create_product(client, seller_token, store_id, name="Remera")
    needle = f"sin-match-{uuid.uuid4().hex}"

    _buyer, buyer_token = _register(client)
    listed = client.get("/products", params={"q": needle}, headers=_auth(buyer_token))
    assert listed.status_code == 200
    body = listed.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_catalog_search_hides_paused_even_if_name_matches(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    unique = f"Remera pausada {uuid.uuid4().hex}"
    product = _create_product(client, seller_token, store_id, name=unique)
    paused = client.post(
        f"/products/{product['id']}/pause",
        headers=_auth(seller_token),
    )
    assert paused.status_code == 200

    _buyer, buyer_token = _register(client)
    listed = client.get("/products", params={"q": unique}, headers=_auth(buyer_token))
    assert listed.status_code == 200
    assert all(item["id"] != product["id"] for item in listed.json()["items"])


def test_catalog_search_blank_q_does_not_filter_by_name(client: TestClient) -> None:
    _seller, seller_token = _register(client)
    store_id, _ = _create_store(client, seller_token)
    shirt = _create_product(client, seller_token, store_id, name="Remera")
    pants = _create_product(client, seller_token, store_id, name="Pantalón")

    _buyer, buyer_token = _register(client)
    listed = client.get("/products", params={"q": "   "}, headers=_auth(buyer_token))
    assert listed.status_code == 200
    ids = [item["id"] for item in listed.json()["items"]]
    assert shirt["id"] in ids
    assert pants["id"] in ids


def test_seller_sets_net_profit_on_create_and_patch(client: TestClient) -> None:
    _email, token = _register(client)
    store_id, _ = _create_store(client, token)
    created = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": "Remera",
            "quantity": "3",
            "price": "199.50",
            "net_profit": "10.00",
            "category": "Ropa",
            "subcategory": "Remeras",
        },
        files={"image": ("remera.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(token),
    )
    assert created.status_code == 201, created.text
    assert created.json()["net_profit"] == "10.00"

    patched = client.patch(
        f"/products/{created.json()['id']}",
        data=_patch_fields(net_profit="12.50"),
        headers=_auth(token),
    )
    assert patched.status_code == 200
    assert patched.json()["net_profit"] == "12.50"


def test_net_profit_omitted_or_empty_is_zero(client: TestClient) -> None:
    _email, token = _register(client)
    store_id, _ = _create_store(client, token)
    omitted = _create_product(client, token, store_id)
    assert omitted["net_profit"] == "0.00"
    empty = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": "Gorra",
            "quantity": "3",
            "price": "199.50",
            "net_profit": "",
            "category": "Ropa",
            "subcategory": "Remeras",
        },
        files={"image": ("remera.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(token),
    )
    assert empty.status_code == 201, empty.text
    assert empty.json()["net_profit"] == "0.00"


def test_net_profit_negative_is_rejected(client: TestClient) -> None:
    _email, token = _register(client)
    store_id, _ = _create_store(client, token)
    response = client.post(
        f"/stores/{store_id}/products",
        data={
            "name": "Remera",
            "quantity": "3",
            "price": "199.50",
            "net_profit": "-1",
            "category": "Ropa",
            "subcategory": "Remeras",
        },
        files={"image": ("remera.png", BytesIO(TINY_PNG), "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Los datos enviados no son válidos"}


