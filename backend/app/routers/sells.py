from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from app.core.db import get_db, is_sqlite
from app.core.security import get_current_user
from app.models.message import SellMessage
from app.models.product import Product
from app.models.sell import Sell
from app.models.store import StoreMembership
from app.models.user import User
from app.schemas.sells import (
    CheckoutRequest,
    CreateMessageRequest,
    CreateSellRequest,
    PatchSellRequest,
    SellItem,
    SellListResponse,
    SellMessageItem,
    SellMessageListResponse,
    TransitionRequest,
)
from app.services.notify import (
    allow_message,
    emit_message,
    emit_sale,
    emit_status,
    eta_for_shipping,
)

router = APIRouter()

_GENERIC = "No se pudo completar la solicitud"
_INVALID = "Los datos enviados no son válidos"

STATUSES = {
    "en_carrito",
    "en_curso",
    "en_viaje",
    "esperando_retiro",
    "completada",
    "cancelada",
    "reembolsada",
}
PAYMENTS = {"tarjeta", "transferencia", "efectivo"}
SELL_SORTS = {
    "id",
    "created_at",
    "product_name",
    "buyer_email",
    "fulfillment",
    "status",
    "subtotal",
}
SELL_ORDERS = {"asc", "desc"}
BUYER_TRANSITIONS = {
    "en_carrito": {"cancelada"},
    "en_curso": {"cancelada"},
}
SELLER_TRANSITIONS = {
    "en_curso": {"en_viaje", "esperando_retiro"},
    "en_viaje": {"completada", "reembolsada"},
    "esperando_retiro": {"completada", "reembolsada"},
    "completada": {"reembolsada"},
}


def _now() -> datetime:
    return datetime.now(UTC)


def _user_by_email(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=401, detail=_GENERIC)
    return user


def _is_store_admin(db: Session, store_id: int, user_id: int) -> bool:
    membership = db.scalar(
        select(StoreMembership).where(
            StoreMembership.store_id == store_id,
            StoreMembership.user_id == user_id,
        )
    )
    return membership is not None and membership.role == "admin"


def _can_manage_product(db: Session, product: Product, user: User) -> bool:
    if product.seller_user_id == user.id:
        return True
    return _is_store_admin(db, product.store_id, user.id)


def _can_manage_sell(db: Session, sell: Sell, user: User) -> bool:
    if sell.seller_user_id == user.id:
        return True
    return _is_store_admin(db, sell.store_id, user.id)


def _lock_product(db: Session, product_id: int) -> Product:
    product = db.scalar(
        select(Product).where(Product.id == product_id).with_for_update()
    )
    if product is None:
        raise HTTPException(status_code=404, detail=_GENERIC)
    _ = product.store.name
    _ = product.seller.email
    return product


def _lock_user(db: Session, user_id: int) -> User:
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(status_code=404, detail=_GENERIC)
    return user


def _message_item(row: SellMessage, viewer_id: int) -> SellMessageItem:
    return SellMessageItem(
        id=row.id,
        sell_id=row.sell_id,
        sender_user_id=row.sender_user_id,
        body=row.body,
        created_at=row.created_at,
        mine=row.sender_user_id == viewer_id,
    )


def _can_view_sell(db: Session, sell: Sell, user: User) -> bool:
    if sell.buyer_user_id == user.id:
        return True
    return _can_manage_sell(db, sell, user)


def _sell_item(
    sell: Sell, viewer: User | None = None, db: Session | None = None
) -> SellItem:
    can_manage = False
    if viewer is not None and db is not None:
        can_manage = _can_manage_sell(db, sell, viewer)
    return SellItem(
        id=sell.id,
        product_id=sell.product_id,
        product_name=sell.product.name,
        store_name=sell.product.store.name,
        buyer_email=sell.buyer.email,
        seller_email=sell.seller.email,
        quantity=sell.quantity,
        unit_price=sell.unit_price,
        subtotal=sell.subtotal,
        fulfillment=sell.fulfillment,  # type: ignore[arg-type]
        payment_method=sell.payment_method,  # type: ignore[arg-type]
        status=sell.status,  # type: ignore[arg-type]
        checkout_id=sell.checkout_id,
        eta_at=sell.eta_at,
        created_at=sell.created_at,
        updated_at=sell.updated_at,
        can_manage=can_manage,
    )


def _load_sell(db: Session, sell_id: int) -> Sell:
    sell = db.scalar(select(Sell).where(Sell.id == sell_id))
    if sell is None:
        raise HTTPException(status_code=404, detail=_GENERIC)
    _ = sell.product.name
    _ = sell.product.store.name
    _ = sell.buyer.email
    _ = sell.seller.email
    return sell


def _fulfillment_ok(product: Product, fulfillment: str) -> bool:
    if fulfillment == "envio":
        return product.ships
    if fulfillment == "retiro":
        return product.pickup
    return False


def _assert_buyable(
    db: Session, product: Product, buyer: User, fulfillment: str
) -> None:
    if product.paused:
        raise HTTPException(status_code=404, detail=_GENERIC)
    if _can_manage_product(db, product, buyer):
        raise HTTPException(status_code=403, detail=_GENERIC)
    if not _fulfillment_ok(product, fulfillment):
        raise HTTPException(status_code=422, detail=_INVALID)


def _apply_paid(db: Session, sell: Sell) -> None:
    product = _lock_product(db, sell.product_id)
    if product.quantity < sell.quantity:
        raise HTTPException(status_code=409, detail=_GENERIC)
    product.quantity -= sell.quantity
    if product.quantity == 0:
        product.paused = True
    seller = _lock_user(db, sell.seller_user_id)
    seller.balance = (seller.balance or Decimal("0")) + sell.subtotal


def _reverse_paid(db: Session, sell: Sell) -> None:
    product = _lock_product(db, sell.product_id)
    product.quantity += sell.quantity
    seller = _lock_user(db, sell.seller_user_id)
    seller.balance = (seller.balance or Decimal("0")) - sell.subtotal


def _checkout_one(
    db: Session,
    sell: Sell,
    payment_method: str,
    checkout_id: str,
) -> None:
    if sell.status != "en_carrito":
        raise HTTPException(status_code=422, detail=_INVALID)
    product = _lock_product(db, sell.product_id)
    _assert_buyable(db, product, sell.buyer, sell.fulfillment)
    if product.quantity < sell.quantity:
        raise HTTPException(status_code=409, detail=_GENERIC)
    sell.unit_price = product.price
    sell.subtotal = product.price * sell.quantity
    sell.payment_method = payment_method
    sell.checkout_id = checkout_id
    sell.status = "en_curso"
    sell.updated_at = _now()
    _apply_paid(db, sell)


@router.post("/sells", response_model=SellItem, status_code=201)
def create_sell(
    payload: CreateSellRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellItem:
    buyer = _user_by_email(db, user["email"])
    product = _lock_product(db, payload.product_id)
    _assert_buyable(db, product, buyer, payload.fulfillment)
    if payload.quantity > product.quantity:
        raise HTTPException(status_code=409, detail=_GENERIC)
    existing = db.scalar(
        select(Sell).where(
            Sell.buyer_user_id == buyer.id,
            Sell.product_id == product.id,
            Sell.status == "en_carrito",
        )
    )
    now = _now()
    if existing is not None:
        existing.quantity = payload.quantity
        existing.fulfillment = payload.fulfillment
        existing.unit_price = product.price
        existing.subtotal = product.price * payload.quantity
        existing.updated_at = now
        db.commit()
        return _sell_item(_load_sell(db, existing.id))
    sell = Sell(
        buyer_user_id=buyer.id,
        seller_user_id=product.seller_user_id,
        product_id=product.id,
        store_id=product.store_id,
        quantity=payload.quantity,
        unit_price=product.price,
        subtotal=product.price * payload.quantity,
        fulfillment=payload.fulfillment,
        payment_method=None,
        status="en_carrito",
        checkout_id=None,
        created_at=now,
        updated_at=now,
    )
    db.add(sell)
    db.commit()
    return _sell_item(_load_sell(db, sell.id))


@router.get("/sells", response_model=SellListResponse)
def list_sells(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
    as_seller: bool = Query(default=False),
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    q: str = Query(default=""),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> SellListResponse:
    needle = q.strip()
    if sort not in SELL_SORTS or order not in SELL_ORDERS or len(needle) > 100:
        raise HTTPException(status_code=422, detail=_INVALID)
    viewer = _user_by_email(db, user["email"])
    query = select(Sell)
    if as_seller:
        admin_stores = select(StoreMembership.store_id).where(
            StoreMembership.user_id == viewer.id,
            StoreMembership.role == "admin",
        )
        query = query.where(
            or_(
                Sell.seller_user_id == viewer.id,
                Sell.store_id.in_(admin_stores),
            )
        )
    else:
        query = query.where(Sell.buyer_user_id == viewer.id)
    if status is not None:
        if status not in STATUSES:
            raise HTTPException(status_code=422, detail=_INVALID)
        query = query.where(Sell.status == status)
    if from_ is not None and to is not None and from_ > to:
        raise HTTPException(status_code=422, detail=_INVALID)
    if from_ is not None:
        start_at = datetime.combine(from_, time.min, tzinfo=UTC)
        query = query.where(Sell.created_at >= start_at)
    if to is not None:
        end_at = datetime.combine(to + timedelta(days=1), time.min, tzinfo=UTC)
        query = query.where(Sell.created_at < end_at)
    buyer = aliased(User)
    if sort in {"product_name", "buyer_email"} or needle:
        query = query.join(Product, Product.id == Sell.product_id)
        query = query.join(buyer, buyer.id == Sell.buyer_user_id)
    if needle:
        pattern = f"%{needle}%"
        if is_sqlite():
            query = query.where(buyer.email.like(pattern))
        else:
            query = query.where(buyer.email.ilike(pattern))
    sort_map = {
        "id": Sell.id,
        "created_at": Sell.created_at,
        "product_name": Product.name,
        "buyer_email": buyer.email,
        "fulfillment": Sell.fulfillment,
        "status": Sell.status,
        "subtotal": Sell.subtotal,
    }
    sort_col = sort_map[sort]
    if order == "desc":
        query = query.order_by(sort_col.desc(), Sell.id.desc())
    else:
        query = query.order_by(sort_col.asc(), Sell.id.asc())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    start = (page - 1) * page_size
    sells = db.scalars(query.offset(start).limit(page_size)).all()
    return SellListResponse(
        items=[_sell_item(item, viewer, db) for item in sells],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sells/{sell_id}", response_model=SellItem)
def get_sell(
    sell_id: int,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellItem:
    viewer = _user_by_email(db, user["email"])
    sell = _load_sell(db, sell_id)
    if sell.status == "en_carrito" or not _can_view_sell(db, sell, viewer):
        raise HTTPException(status_code=404, detail=_GENERIC)
    return _sell_item(sell, viewer, db)


@router.get("/sells/{sell_id}/messages", response_model=SellMessageListResponse)
def list_messages(
    sell_id: int,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> SellMessageListResponse:
    viewer = _user_by_email(db, user["email"])
    sell = _load_sell(db, sell_id)
    if sell.status == "en_carrito" or not _can_view_sell(db, sell, viewer):
        raise HTTPException(status_code=404, detail=_GENERIC)
    query = (
        select(SellMessage)
        .where(SellMessage.sell_id == sell.id)
        .order_by(SellMessage.id.asc())
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    start = (page - 1) * page_size
    rows = db.scalars(query.offset(start).limit(page_size)).all()
    return SellMessageListResponse(
        items=[_message_item(row, viewer.id) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/sells/{sell_id}/messages", response_model=SellMessageItem, status_code=201
)
async def create_message(
    sell_id: int,
    payload: CreateMessageRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellMessageItem:
    viewer = _user_by_email(db, user["email"])
    sell = _load_sell(db, sell_id)
    if not _can_view_sell(db, sell, viewer):
        raise HTTPException(status_code=403, detail=_GENERIC)
    if sell.status == "en_carrito":
        raise HTTPException(status_code=422, detail=_INVALID)
    if not allow_message(viewer.id):
        raise HTTPException(status_code=429, detail=_GENERIC)
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail=_INVALID)
    row = SellMessage(
        sell_id=sell.id,
        sender_user_id=viewer.id,
        body=body,
        created_at=_now(),
    )
    db.add(row)
    db.commit()
    item = _message_item(row, viewer.id)
    await emit_message(
        db,
        sell,
        viewer,
        {"message": _message_item(row, -1).model_dump(mode="json")},
    )
    return item


@router.patch("/sells/{sell_id}", response_model=SellItem)
def patch_sell(
    sell_id: int,
    payload: PatchSellRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellItem:
    buyer = _user_by_email(db, user["email"])
    sell = _load_sell(db, sell_id)
    if sell.buyer_user_id != buyer.id or sell.status != "en_carrito":
        raise HTTPException(status_code=403, detail=_GENERIC)
    product = _lock_product(db, sell.product_id)
    quantity = payload.quantity if payload.quantity is not None else sell.quantity
    fulfillment = payload.fulfillment or sell.fulfillment
    _assert_buyable(db, product, buyer, fulfillment)
    if quantity > product.quantity:
        raise HTTPException(status_code=409, detail=_GENERIC)
    sell.quantity = quantity
    sell.fulfillment = fulfillment
    sell.unit_price = product.price
    sell.subtotal = product.price * quantity
    sell.updated_at = _now()
    db.commit()
    return _sell_item(_load_sell(db, sell.id))


@router.post("/sells/checkout", response_model=SellListResponse)
async def checkout(
    payload: CheckoutRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellListResponse:
    if payload.payment_method not in PAYMENTS:
        raise HTTPException(status_code=422, detail=_INVALID)
    if payload.sell_ids and payload.items:
        raise HTTPException(status_code=422, detail=_INVALID)
    buyer = _user_by_email(db, user["email"])
    checkout_id = uuid4().hex
    sells: list[Sell] = []
    if payload.items:
        for item in payload.items:
            product = _lock_product(db, item.product_id)
            _assert_buyable(db, product, buyer, item.fulfillment)
            now = _now()
            sell = Sell(
                buyer_user_id=buyer.id,
                seller_user_id=product.seller_user_id,
                product_id=product.id,
                store_id=product.store_id,
                quantity=item.quantity,
                unit_price=product.price,
                subtotal=product.price * item.quantity,
                fulfillment=item.fulfillment,
                payment_method=None,
                status="en_carrito",
                checkout_id=None,
                created_at=now,
                updated_at=now,
            )
            db.add(sell)
            db.flush()
            sells.append(sell)
    elif payload.sell_ids:
        for sell_id in payload.sell_ids:
            sell = _load_sell(db, sell_id)
            if sell.buyer_user_id != buyer.id:
                raise HTTPException(status_code=403, detail=_GENERIC)
            sells.append(sell)
    else:
        sells = list(
            db.scalars(
                select(Sell).where(
                    Sell.buyer_user_id == buyer.id,
                    Sell.status == "en_carrito",
                )
            ).all()
        )
    if not sells:
        raise HTTPException(status_code=422, detail=_INVALID)
    for sell in sells:
        _checkout_one(db, sell, payload.payment_method, checkout_id)
    db.commit()
    for sell in sells:
        loaded = _load_sell(db, sell.id)
        await emit_sale(db, loaded, buyer, loaded.product)
    return SellListResponse(
        items=[_sell_item(_load_sell(db, item.id)) for item in sells],
        total=len(sells),
        page=1,
        page_size=len(sells),
    )


@router.post("/sells/{sell_id}/transition", response_model=SellItem)
async def transition_sell(
    sell_id: int,
    payload: TransitionRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellItem:
    viewer = _user_by_email(db, user["email"])
    sell = _load_sell(db, sell_id)
    target = payload.status
    if target not in STATUSES:
        raise HTTPException(status_code=422, detail=_INVALID)
    allowed: set[str] = set()
    if sell.buyer_user_id == viewer.id:
        allowed |= BUYER_TRANSITIONS.get(sell.status, set())
    if _can_manage_sell(db, sell, viewer):
        allowed |= SELLER_TRANSITIONS.get(sell.status, set())
    if target not in allowed:
        raise HTTPException(status_code=422, detail=_INVALID)
    if target == "en_viaje" and sell.fulfillment != "envio":
        raise HTTPException(status_code=422, detail=_INVALID)
    if target == "esperando_retiro" and sell.fulfillment != "retiro":
        raise HTTPException(status_code=422, detail=_INVALID)
    previous = sell.status
    sell.status = target
    sell.updated_at = _now()
    if target == "en_viaje":
        sell.eta_at = eta_for_shipping()
    if previous == "en_curso" and target == "cancelada":
        _reverse_paid(db, sell)
    if target == "reembolsada":
        _reverse_paid(db, sell)
    db.commit()
    item = _sell_item(_load_sell(db, sell.id), viewer, db)
    await emit_status(
        db,
        sell,
        viewer,
        {"sell": item.model_dump(mode="json")},
    )
    return item
