from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db, is_sqlite
from app.core.security import get_current_user
from app.models.product import Product
from app.models.sell import Sell
from app.models.store import StoreMembership
from app.models.user import User
from app.schemas.dashboard import (
    DashboardDelta,
    DashboardPrevious,
    DashboardProductItem,
    DashboardResponse,
    DashboardSellerItem,
    MixSlice,
    NetProfitDay,
    OpenByStatus,
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


def _delta_pct(current: Decimal | int, previous: Decimal | int) -> Decimal | None:
    prev = Decimal(str(previous))
    if prev == 0:
        return None
    return ((Decimal(str(current)) - prev) / prev * Decimal("100")).quantize(
        Decimal("0.1")
    )


def _day_utc(value: datetime | date) -> date:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC).date()
        return value.astimezone(UTC).date()
    return value


def _coerce_day(value: datetime | date | str) -> date:
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    return _day_utc(value)


def _day_bucket():
    if is_sqlite():
        return func.strftime("%Y-%m-%d", Sell.updated_at)
    return func.date_trunc("day", Sell.updated_at)


def _profit_series(
    db: Session,
    scope,
    since: datetime,
    until: datetime,
) -> list[NetProfitDay]:
    day_col = _day_bucket()
    rows = db.execute(
        select(
            day_col,
            func.coalesce(func.sum(Product.net_profit * Sell.quantity), 0),
            func.coalesce(func.sum(Sell.subtotal), 0),
        )
        .join(Product, Product.id == Sell.product_id)
        .where(
            scope,
            Sell.status == "completada",
            Sell.updated_at >= since,
        )
        .group_by(day_col)
    ).all()
    by_profit: dict[date, Decimal] = {}
    by_amount: dict[date, Decimal] = {}
    for raw_day, profit, gmv in rows:
        key = _coerce_day(raw_day)
        by_profit[key] = _money(profit)
        by_amount[key] = _money(gmv)
    series: list[NetProfitDay] = []
    cumulative = _ZERO
    cursor = _day_utc(since)
    end = _day_utc(until)
    while cursor <= end:
        daily = by_profit.get(cursor, _ZERO)
        cumulative = _money(cumulative + daily)
        series.append(
            NetProfitDay(
                date=cursor,
                amount=by_amount.get(cursor, _ZERO),
                net_profit=daily,
                cumulative=cumulative,
            )
        )
        cursor += timedelta(days=1)
    return series


def _open_by_status(db: Session, scope) -> OpenByStatus:
    rows = db.execute(
        select(Sell.status, func.count(Sell.id))
        .where(scope, Sell.status.in_(_OPEN))
        .group_by(Sell.status)
    ).all()
    counts = {status: int(count) for status, count in rows}
    return OpenByStatus(
        en_curso=counts.get("en_curso", 0),
        en_viaje=counts.get("en_viaje", 0),
        esperando_retiro=counts.get("esperando_retiro", 0),
    )


def _mix(db: Session, scope, since: datetime, column) -> list[MixSlice]:
    rows = db.execute(
        select(
            column,
            func.count(Sell.id),
            func.coalesce(func.sum(Sell.subtotal), 0),
        )
        .where(
            scope,
            Sell.status == "completada",
            Sell.updated_at >= since,
        )
        .group_by(column)
    ).all()
    slices: list[MixSlice] = []
    for key, count, amount in rows:
        label = key if isinstance(key, str) and key else "otro"
        slices.append(MixSlice(key=label, count=int(count), amount=_money(amount)))
    slices.sort(key=lambda item: item.amount, reverse=True)
    return slices


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

    now = _now()
    since = now - timedelta(days=days)
    previous_since = since - timedelta(days=days)
    scope = _scope(viewer.id)

    def _completed_window(start: datetime, end: datetime | None):
        filters = [
            scope,
            Sell.status == "completada",
            Sell.updated_at >= start,
        ]
        if end is not None:
            filters.append(Sell.updated_at < end)
        return db.execute(
            select(
                func.count(Sell.id),
                func.coalesce(func.sum(Sell.subtotal), 0),
                func.coalesce(func.sum(Sell.quantity), 0),
                func.coalesce(func.sum(Product.net_profit * Sell.quantity), 0),
            )
            .join(Product, Product.id == Sell.product_id)
            .where(*filters)
        ).one()

    completed = _completed_window(since, None)
    prior = _completed_window(previous_since, since)
    sales_count = int(completed[0] or 0)
    total_amount = _money(completed[1])
    units_sold = int(completed[2] or 0)
    net_profit_total = _money(completed[3])
    average_ticket = _money(total_amount / sales_count) if sales_count else _ZERO
    previous_sales = int(prior[0] or 0)
    previous_amount = _money(prior[1])
    previous_units = int(prior[2] or 0)
    previous_profit = _money(prior[3])
    previous_ticket = (
        _money(previous_amount / previous_sales) if previous_sales else _ZERO
    )

    open_orders = (
        db.scalar(select(func.count(Sell.id)).where(scope, Sell.status.in_(_OPEN))) or 0
    )

    def _cancelled_window(start: datetime, end: datetime | None) -> int:
        filters = [
            scope,
            Sell.status == "cancelada",
            Sell.updated_at >= start,
        ]
        if end is not None:
            filters.append(Sell.updated_at < end)
        return int(db.scalar(select(func.count(Sell.id)).where(*filters)) or 0)

    cancelled_count = _cancelled_window(since, None)
    previous_cancelled = _cancelled_window(previous_since, since)
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
        net_profit_series=_profit_series(db, scope, since, now),
        open_by_status=_open_by_status(db, scope),
        fulfillment_mix=_mix(db, scope, since, Sell.fulfillment),
        payment_mix=_mix(db, scope, since, Sell.payment_method),
        previous=DashboardPrevious(
            from_=previous_since,
            sales_count=previous_sales,
            total_amount=previous_amount,
            net_profit_total=previous_profit,
            units_sold=previous_units,
            average_ticket=previous_ticket,
            cancelled_count=previous_cancelled,
        ),
        delta=DashboardDelta(
            sales_count_pct=_delta_pct(sales_count, previous_sales),
            total_amount_pct=_delta_pct(total_amount, previous_amount),
            net_profit_total_pct=_delta_pct(net_profit_total, previous_profit),
            units_sold_pct=_delta_pct(units_sold, previous_units),
            average_ticket_pct=_delta_pct(average_ticket, previous_ticket),
            cancelled_count_pct=_delta_pct(cancelled_count, previous_cancelled),
        ),
    )
