from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, extract, func, literal, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.product import Product, ProductAnswer, ProductQuestion
from app.models.store import StoreMembership
from app.models.user import User
from app.schemas.questions import (
    SellerQuestionItem,
    SellerQuestionListResponse,
)

router = APIRouter()

_GENERIC = "No se pudo completar la solicitud"
_INVALID = "Los datos enviados no son válidos"
_ZERO = Decimal("0.00")
_STATUSES = {"pending", "answered", "all"}
_SORTS = {"score", "wait", "net_profit", "created_at", "name"}
_ORDERS = {"asc", "desc"}


def _user_by_email(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=401, detail=_GENERIC)
    return user


def _money(value: Decimal | float | int | None) -> Decimal:
    if value is None:
        return _ZERO
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _scope(viewer_id: int):
    admin_stores = select(StoreMembership.store_id).where(
        StoreMembership.user_id == viewer_id,
        StoreMembership.role == "admin",
    )
    return or_(
        Product.seller_user_id == viewer_id,
        Product.store_id.in_(admin_stores),
    )


@router.get("/questions", response_model=SellerQuestionListResponse)
def list_seller_questions(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: str = Query("pending"),
    sort: str = Query("score"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1),
) -> SellerQuestionListResponse:
    if (
        status not in _STATUSES
        or sort not in _SORTS
        or order not in _ORDERS
        or page_size > get_settings().max_page_size
    ):
        raise HTTPException(status_code=422, detail=_INVALID)
    viewer = _user_by_email(db, user["email"])
    membership = db.scalar(
        select(StoreMembership.id).where(StoreMembership.user_id == viewer.id)
    )
    if membership is None:
        raise HTTPException(status_code=403, detail=_GENERIC)

    now = datetime.now(UTC)
    age_hours = extract("epoch", now - ProductQuestion.created_at) / 3600.0
    wait_expr = case((ProductAnswer.id.is_(None), age_hours), else_=literal(0))
    score_expr = wait_expr + Product.net_profit
    sort_map = {
        "score": score_expr,
        "wait": wait_expr,
        "net_profit": Product.net_profit,
        "created_at": ProductQuestion.created_at,
        "name": Product.name,
    }
    sort_col = sort_map[sort]
    if order == "desc":
        sort_col = sort_col.desc()
    else:
        sort_col = sort_col.asc()

    query = (
        select(ProductQuestion, Product, ProductAnswer)
        .join(Product, Product.id == ProductQuestion.product_id)
        .outerjoin(ProductAnswer, ProductAnswer.question_id == ProductQuestion.id)
        .where(_scope(viewer.id))
    )
    if status == "pending":
        query = query.where(ProductAnswer.id.is_(None))
    elif status == "answered":
        query = query.where(ProductAnswer.id.isnot(None))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    start = (page - 1) * page_size
    rows = db.execute(
        query.order_by(sort_col, ProductQuestion.id.desc())
        .offset(start)
        .limit(page_size)
    ).all()

    items: list[SellerQuestionItem] = []
    for question, product, answer in rows:
        wait_hours = (
            _ZERO
            if answer is not None
            else _money((now - question.created_at).total_seconds() / 3600)
        )
        profit = _money(product.net_profit)
        items.append(
            SellerQuestionItem(
                id=question.id,
                product_id=product.id,
                product_name=product.name,
                text=question.text,
                answer=None if answer is None else answer.text,
                created_at=question.created_at,
                wait_hours=wait_hours,
                net_profit=profit,
                score=_money(wait_hours + profit),
            )
        )
    return SellerQuestionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
