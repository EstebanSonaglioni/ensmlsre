from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.product import Product
from app.models.sell import Sell
from app.models.store import StoreMembership
from app.models.user import User
from app.schemas.dashboard import (
    DashboardProductItem,
    DashboardResponse,
    DashboardSellerItem,
)

router = APIRouter()

_GENERIC = "No se pudo completar la solicitud"
_INVALID = "Los datos enviados no son válidos"
_ZERO = Decimal("0.00")
_OPEN = ("en_curso", "en_viaje", "esperando_retiro")
_ALLOWED_DAYS = {7, 30, 90}


def _now() -> datetime:
    return datetime.now(UTC)


def _user_by_email(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=401, detail=_GENERIC)
    return user


def _money(value: Decimal | int | None) -> Decimal:
    if value is None:
        return _ZERO
    return Decimal(value).quantize(Decimal("0.01"))


def _scope(viewer_id: int):
    admin_stores = select(StoreMembership.store_id).where(
        StoreMembership.user_id == viewer_id,
        StoreMembership.role == "admin",
    )
    return or_(
        Sell.seller_user_id == viewer_id,
        Sell.store_id.in_(admin_stores),
    )


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30),
) -> DashboardResponse:
    if days not in _ALLOWED_DAYS:
        raise HTTPException(status_code=422, detail=_INVALID)
    viewer = _user_by_email(db, user["email"])
    membership = db.scalar(
        select(StoreMembership.id).where(StoreMembership.user_id == viewer.id)
    )
    if membership is None:
        raise HTTPException(status_code=403, detail=_GENERIC)

    since = _now() - timedelta(days=days)
    scope = _scope(viewer.id)
    completed = db.execute(
        select(
            func.count(Sell.id),
            func.coalesce(func.sum(Sell.subtotal), 0),
            func.coalesce(func.sum(Sell.quantity), 0),
            func.coalesce(func.sum(Product.net_profit * Sell.quantity), 0),
        )
        .join(Product, Product.id == Sell.product_id)
        .where(
            scope,
            Sell.status == "completada",
            Sell.updated_at >= since,
        )
    ).one()
    sales_count = int(completed[0] or 0)
    total_amount = _money(completed[1])
    units_sold = int(completed[2] or 0)
    net_profit_total = _money(completed[3])
    average_ticket = (
        _money(total_amount / sales_count) if sales_count else _ZERO
    )

    open_orders = db.scalar(
        select(func.count(Sell.id)).where(scope, Sell.status.in_(_OPEN))
    ) or 0
    cancelled_count = db.scalar(
        select(func.count(Sell.id)).where(
            scope,
            Sell.status == "cancelada",
            Sell.updated_at >= since,
        )
    ) or 0
    refunded = db.execute(
        select(
            func.count(Sell.id),
            func.coalesce(func.sum(Sell.subtotal), 0),
        ).where(
            scope,
            Sell.status == "reembolsada",
            Sell.updated_at >= since,
        )
    ).one()

    product_rows = db.execute(
        select(
            Product.id,
            Product.name,
            func.coalesce(func.sum(Sell.quantity), 0),
            func.coalesce(func.sum(Sell.subtotal), 0),
            func.coalesce(func.sum(Product.net_profit * Sell.quantity), 0),
        )
        .join(Product, Product.id == Sell.product_id)
        .where(
            scope,
            Sell.status == "completada",
            Sell.updated_at >= since,
        )
        .group_by(Product.id, Product.name)
        .order_by(func.sum(Sell.quantity).desc(), Product.id.desc())
        .limit(10)
    ).all()

    is_admin = db.scalar(
        select(StoreMembership.id).where(
            StoreMembership.user_id == viewer.id,
            StoreMembership.role == "admin",
        )
    )
    sellers: list[DashboardSellerItem] = []
    if is_admin is not None:
        seller_rows = db.execute(
            select(
                User.email,
                func.count(Sell.id),
                func.coalesce(func.sum(Sell.subtotal), 0),
            )
            .join(User, User.id == Sell.seller_user_id)
            .where(
                scope,
                Sell.status == "completada",
                Sell.updated_at >= since,
            )
            .group_by(User.id, User.email)
            .order_by(func.sum(Sell.subtotal).desc(), User.id.desc())
            .limit(10)
        ).all()
        sellers = [
            DashboardSellerItem(
                email=email,
                sales_count=int(count),
                amount=_money(amount),
            )
            for email, count, amount in seller_rows
        ]

    return DashboardResponse(
        days=days,
        from_=since,
        sales_count=sales_count,
        total_amount=total_amount,
        net_profit_total=net_profit_total,
        units_sold=units_sold,
        average_ticket=average_ticket,
        open_orders=int(open_orders),
        cancelled_count=int(cancelled_count),
        refunded_count=int(refunded[0] or 0),
        refunded_amount=_money(refunded[1]),
        top_products=[
            DashboardProductItem(
                product_id=product_id,
                name=name,
                units=int(units),
                amount=_money(amount),
                net_profit=_money(profit),
            )
            for product_id, name, units, amount, profit in product_rows
        ],
        sellers=sellers,
    )
