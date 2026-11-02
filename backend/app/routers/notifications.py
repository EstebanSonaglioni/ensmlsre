from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.notification import Notification
from app.models.sell import Sell
from app.models.user import User
from app.schemas.sells import NotificationItem, NotificationListResponse

router = APIRouter()

_GENERIC = "No se pudo completar la solicitud"


def _user_by_email(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=401, detail=_GENERIC)
    return user


def _item(row: Notification, viewer: User, db: Session) -> NotificationItem:
    as_seller = row.kind in {"pregunta", "venta"}
    if row.sell_id is not None:
        sell = db.scalar(select(Sell).where(Sell.id == row.sell_id))
        as_seller = sell is not None and sell.buyer_user_id != viewer.id
    return NotificationItem(
        id=row.id,
        sell_id=row.sell_id,
        product_id=row.product_id,
        kind=row.kind,  # type: ignore[arg-type]
        title=row.title,
        body=row.body,
        as_seller=as_seller,
        read_at=row.read_at,
        created_at=row.created_at,
    )


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    unread: bool = Query(default=False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> NotificationListResponse:
    viewer = _user_by_email(db, user["email"])
    query = select(Notification).where(Notification.user_id == viewer.id)
    if unread:
        query = query.where(Notification.read_at.is_(None))
    query = query.order_by(Notification.id.desc())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    unread_count = (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == viewer.id,
                Notification.read_at.is_(None),
            )
        )
        or 0
    )
    start = (page - 1) * page_size
    rows = db.scalars(query.offset(start).limit(page_size)).all()
    return NotificationListResponse(
        items=[_item(row, viewer, db) for row in rows],
        total=total,
        unread=unread_count,
        page=page,
        page_size=page_size,
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationItem)
def read_notification(
    notification_id: int,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationItem:
    viewer = _user_by_email(db, user["email"])
    row = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == viewer.id,
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail=_GENERIC)
    if row.read_at is None:
        row.read_at = datetime.now(UTC)
        db.commit()
    return _item(row, viewer, db)


@router.post("/notifications/read-all")
def read_all_notifications(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    viewer = _user_by_email(db, user["email"])
    now = datetime.now(UTC)
    rows = db.scalars(
        select(Notification).where(
            Notification.user_id == viewer.id,
            Notification.read_at.is_(None),
        )
    ).all()
    for row in rows:
        row.read_at = now
    db.commit()
    return {"detail": "Listo"}
