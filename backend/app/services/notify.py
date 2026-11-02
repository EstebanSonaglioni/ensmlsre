from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from time import monotonic

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ws_hub import hub
from app.models.notification import Notification
from app.models.product import Product
from app.models.sell import Sell
from app.models.store import StoreMembership
from app.models.user import User

_MESSAGE_WINDOW = 60.0
_MESSAGE_LIMIT = 20
_message_hits: dict[int, deque[float]] = defaultdict(deque)


def allow_message(user_id: int) -> bool:
    now = monotonic()
    hits = _message_hits[user_id]
    while hits and now - hits[0] > _MESSAGE_WINDOW:
        hits.popleft()
    if len(hits) >= _MESSAGE_LIMIT:
        return False
    hits.append(now)
    return True


def counterpart_ids(sell: Sell, sender: User) -> list[int]:
    ids: set[int] = {sell.buyer_user_id, sell.seller_user_id}
    ids.discard(sender.id)
    return list(ids)


def manager_ids(db: Session, product: Product) -> list[int]:
    ids: set[int] = {product.seller_user_id}
    admins = db.scalars(
        select(StoreMembership.user_id).where(
            StoreMembership.store_id == product.store_id,
            StoreMembership.role == "admin",
        )
    )
    ids.update(admins)
    return list(ids)


def _notification_item(
    row: Notification,
    *,
    as_seller: bool,
) -> dict:
    return {
        "id": row.id,
        "sell_id": row.sell_id,
        "product_id": row.product_id,
        "kind": row.kind,
        "title": row.title,
        "body": row.body,
        "as_seller": as_seller,
        "read_at": row.read_at.isoformat() if row.read_at else None,
        "created_at": row.created_at.isoformat(),
    }


async def emit_message(
    db: Session,
    sell: Sell,
    sender: User,
    payload: dict,
) -> None:
    await _emit(
        db,
        counterpart_ids(sell, sender),
        sender,
        kind="mensaje",
        title="Nuevo mensaje",
        body="Tenés un mensaje en una orden",
        sell_id=sell.id,
        product_id=sell.product_id,
        as_seller_for=lambda user_id: user_id != sell.buyer_user_id,
        skip_if_watching_sell=sell.id,
        live_event={"type": "message", **payload},
    )


async def emit_status(
    db: Session,
    sell: Sell,
    sender: User,
    payload: dict,
) -> None:
    await _emit(
        db,
        counterpart_ids(sell, sender),
        sender,
        kind="estado",
        title="Actualización de orden",
        body="El estado de una orden cambió",
        sell_id=sell.id,
        product_id=sell.product_id,
        as_seller_for=lambda user_id: user_id != sell.buyer_user_id,
        skip_if_watching_sell=sell.id,
        live_event={"type": "status", **payload},
    )


async def emit_question(
    db: Session,
    product: Product,
    sender: User,
    payload: dict,
) -> None:
    event = {
        "type": "question",
        "product_id": product.id,
        "question": payload,
    }
    for user_id in hub.product_watchers(product.id):
        if user_id != sender.id:
            await hub.send_user(user_id, event)
    await _emit(
        db,
        manager_ids(db, product),
        sender,
        kind="pregunta",
        title="Nueva pregunta",
        body="Hay una pregunta en una publicación",
        sell_id=None,
        product_id=product.id,
        as_seller_for=lambda _user_id: True,
        skip_if_watching_product=product.id,
        live_event=None,
    )


async def emit_answer(
    db: Session,
    product: Product,
    sender: User,
    asker_user_id: int,
    payload: dict,
) -> None:
    event = {
        "type": "answer",
        "product_id": product.id,
        "question": payload,
    }
    for user_id in hub.product_watchers(product.id):
        if user_id != sender.id:
            await hub.send_user(user_id, event)
    await _emit(
        db,
        [asker_user_id],
        sender,
        kind="respuesta",
        title="Nueva respuesta",
        body="Respondieron una pregunta de una publicación",
        sell_id=None,
        product_id=product.id,
        as_seller_for=lambda _user_id: False,
        skip_if_watching_product=product.id,
        live_event=None,
    )


async def emit_sale(
    db: Session,
    sell: Sell,
    sender: User,
    product: Product,
) -> None:
    recipients = set(manager_ids(db, product))
    recipients.discard(sender.id)
    await _emit(
        db,
        list(recipients),
        sender,
        kind="venta",
        title="Nueva venta",
        body="Se confirmó una compra de una publicación",
        sell_id=sell.id,
        product_id=product.id,
        as_seller_for=lambda _user_id: True,
        skip_if_watching_sell=None,
        live_event=None,
    )


async def _emit(
    db: Session,
    user_ids: list[int],
    sender: User,
    *,
    kind: str,
    title: str,
    body: str,
    sell_id: int | None,
    product_id: int | None,
    as_seller_for,
    skip_if_watching_sell: int | None = None,
    skip_if_watching_product: int | None = None,
    live_event: dict | None,
) -> None:
    now = datetime.now(UTC)
    for user_id in user_ids:
        if user_id == sender.id:
            continue
        watching_sell = (
            skip_if_watching_sell is not None
            and hub.is_watching(user_id, skip_if_watching_sell)
        )
        watching_product = (
            skip_if_watching_product is not None
            and hub.is_watching_product(user_id, skip_if_watching_product)
        )
        if watching_sell and live_event is not None:
            await hub.send_user(user_id, live_event)
            continue
        if watching_sell or watching_product:
            continue
        row = Notification(
            user_id=user_id,
            sell_id=sell_id,
            product_id=product_id,
            kind=kind,
            title=title,
            body=body,
            read_at=None,
            created_at=now,
        )
        db.add(row)
        db.flush()
        await hub.send_user(
            user_id,
            {
                "type": "notification",
                "notification": _notification_item(
                    row, as_seller=as_seller_for(user_id)
                ),
            },
        )
    db.commit()


def eta_for_shipping() -> datetime:
    return datetime.now(UTC) + timedelta(hours=48)
