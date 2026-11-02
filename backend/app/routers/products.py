from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.notification import Notification
from app.models.product import Product, ProductAnswer, ProductQuestion
from app.models.store import StoreMembership
from app.models.user import User
from app.schemas.products import (
    CreateAnswerRequest,
    CreateQuestionRequest,
    ProductDetailResponse,
    ProductItem,
    ProductListResponse,
    ProductQuestionItem,
)
from app.services.notify import emit_answer, emit_question

router = APIRouter()

_GENERIC = "No se pudo completar la solicitud"


def _user_by_email(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=401, detail=_GENERIC)
    return user


def _membership(db: Session, store_id: int, user_id: int) -> StoreMembership | None:
    return db.scalar(
        select(StoreMembership).where(
            StoreMembership.store_id == store_id,
            StoreMembership.user_id == user_id,
        )
    )


def _is_store_admin(db: Session, store_id: int, user_id: int) -> bool:
    membership = _membership(db, store_id, user_id)
    return membership is not None and membership.role == "admin"


def _can_view(db: Session, product: Product, user: User) -> bool:
    if not product.paused:
        return True
    if product.seller_user_id == user.id:
        return True
    return _is_store_admin(db, product.store_id, user.id)


def _can_pause(db: Session, product: Product, user: User) -> bool:
    if product.seller_user_id == user.id:
        return True
    return _is_store_admin(db, product.store_id, user.id)


def _images_dir() -> Path:
    path = Path(get_settings().PRODUCT_IMAGES_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _media_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data.startswith(b"GIF8"):
        return "image/gif"
    return None


def _parse_money(raw: str) -> Decimal:
    text = raw.strip()
    if not text:
        return Decimal("0.00")
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise HTTPException(
            status_code=422, detail="Los datos enviados no son válidos"
        ) from None
    if amount < 0:
        raise HTTPException(status_code=422, detail="Los datos enviados no son válidos")
    return amount.quantize(Decimal("0.01"))


def _parse_qty_price(quantity: str, price: str) -> tuple[int, Decimal]:
    try:
        qty = int(quantity)
    except ValueError:
        raise HTTPException(
            status_code=422, detail="Los datos enviados no son válidos"
        ) from None
    amount = _parse_money(price)
    if qty < 0:
        raise HTTPException(status_code=422, detail="Los datos enviados no son válidos")
    return qty, amount


def _parse_flag(raw: str) -> bool:
    value = raw.strip().lower()
    if value in {"true", "1", "on", "si", "sí"}:
        return True
    if value in {"false", "0", "off", "no"}:
        return False
    raise HTTPException(status_code=422, detail="Los datos enviados no son válidos")


async def _read_image(image: UploadFile) -> bytes:
    limit = get_settings().max_upload_bytes
    data = await image.read(limit + 1)
    if not data or len(data) > limit or _media_type(data) is None:
        raise HTTPException(status_code=422, detail="Los datos enviados no son válidos")
    return data


def _write_image(data: bytes) -> str:
    name = uuid4().hex
    dest = _images_dir() / name
    dest.write_bytes(data)
    return name


def _image_file(product: Product) -> Path:
    stored = Path(product.image_path)
    if stored.is_file():
        return stored
    return _images_dir() / stored.name


def _product_item(product: Product, *, include_profit: bool = False) -> ProductItem:
    return ProductItem(
        id=product.id,
        store_id=product.store_id,
        store_name=product.store.name,
        name=product.name,
        quantity=product.quantity,
        price=product.price,
        net_profit=product.net_profit if include_profit else None,
        category=product.category,
        subcategory=product.subcategory,
        paused=product.paused,
        ships=product.ships,
        pickup=product.pickup,
    )


def _asker_label(user: User) -> str:
    name = (user.display_name or "").strip()
    return name if name else "Comprador"


def _question_item(
    question: ProductQuestion,
    answer_text: str | None,
    *,
    reveal_email: bool,
    asker: User | None = None,
) -> ProductQuestionItem:
    person = asker or question.asker
    return ProductQuestionItem(
        id=question.id,
        asker_label=_asker_label(person),
        asker_email=person.email if reveal_email else None,
        text=question.text,
        answer=answer_text,
    )


def _load_product(db: Session, product_id: int) -> Product:
    product = db.scalar(
        select(Product)
        .where(Product.id == product_id)
        .execution_options(populate_existing=True)
    )
    if product is None:
        raise HTTPException(status_code=404, detail=_GENERIC)
    _ = product.store.name
    _ = product.seller.id
    return product


@router.post("/stores/{store_id}/products", response_model=ProductItem, status_code=201)
async def create_product(
    store_id: int,
    name: str = Form(min_length=1),
    quantity: str = Form(),
    price: str = Form(),
    category: str = Form(min_length=1),
    subcategory: str = Form(min_length=1),
    ships: str = Form("true"),
    pickup: str = Form("true"),
    net_profit: str = Form("0"),
    image: UploadFile = File(),
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductItem:
    seller = _user_by_email(db, user["email"])
    membership = _membership(db, store_id, seller.id)
    if membership is None:
        raise HTTPException(status_code=403, detail=_GENERIC)
    qty, amount = _parse_qty_price(quantity, price)
    profit = _parse_money(net_profit)
    ships_flag = _parse_flag(ships)
    pickup_flag = _parse_flag(pickup)
    if not ships_flag and not pickup_flag:
        raise HTTPException(status_code=422, detail="Los datos enviados no son válidos")
    if not image.filename:
        raise HTTPException(status_code=422, detail="Los datos enviados no son válidos")
    dest = _write_image(await _read_image(image))
    product = Product(
        store_id=store_id,
        seller_user_id=seller.id,
        name=name.strip(),
        quantity=qty,
        price=amount,
        net_profit=profit,
        category=category.strip(),
        subcategory=subcategory.strip(),
        image_path=dest,
        paused=False,
        ships=ships_flag,
        pickup=pickup_flag,
    )
    db.add(product)
    db.commit()
    return _product_item(_load_product(db, product.id), include_profit=True)


def _paginate_products(
    db: Session,
    query: Select[tuple[Product]],
    page: int,
    page_size: int,
    *,
    include_profit: bool = False,
) -> ProductListResponse:
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    start = (page - 1) * page_size
    products = db.scalars(query.offset(start).limit(page_size)).all()
    return ProductListResponse(
        items=[_product_item(item, include_profit=include_profit) for item in products],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/products/mine", response_model=ProductListResponse)
def list_my_products(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> ProductListResponse:
    viewer = _user_by_email(db, user["email"])
    store_ids = select(StoreMembership.store_id).where(
        StoreMembership.user_id == viewer.id,
    )
    query = (
        select(Product)
        .where(
            or_(
                Product.seller_user_id == viewer.id,
                Product.store_id.in_(store_ids),
            )
        )
        .order_by(Product.id.desc())
    )
    return _paginate_products(db, query, page, page_size, include_profit=True)


@router.get("/products", response_model=ProductListResponse)
def list_products(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str = Query("", max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> ProductListResponse:
    _user_by_email(db, user["email"])
    query = select(Product).where(Product.paused.is_(False))
    needle = q.strip().casefold()
    if needle:
        query = query.where(
            func.lower(Product.name).contains(needle, autoescape=True),
        )
    query = query.order_by(Product.id.desc())
    return _paginate_products(db, query, page, page_size)


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
def get_product(
    product_id: int,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductDetailResponse:
    viewer = _user_by_email(db, user["email"])
    product = _load_product(db, product_id)
    if not _can_view(db, product, viewer):
        raise HTTPException(status_code=404, detail=_GENERIC)
    questions = db.scalars(
        select(ProductQuestion)
        .where(ProductQuestion.product_id == product.id)
        .order_by(ProductQuestion.id.asc())
    ).all()
    can_manage = _can_pause(db, product, viewer)
    items: list[ProductQuestionItem] = []
    for question in questions:
        answer = db.scalar(
            select(ProductAnswer).where(ProductAnswer.question_id == question.id)
        )
        items.append(
            _question_item(
                question,
                answer.text if answer is not None else None,
                reveal_email=can_manage,
            )
        )
    base = _product_item(product, include_profit=can_manage)
    return ProductDetailResponse(
        **base.model_dump(),
        questions=items,
        can_manage=can_manage,
    )


@router.patch("/products/{product_id}", response_model=ProductItem)
async def update_product(
    product_id: int,
    name: str = Form(min_length=1),
    quantity: str = Form(),
    price: str = Form(),
    category: str = Form(min_length=1),
    subcategory: str = Form(min_length=1),
    ships: str = Form("true"),
    pickup: str = Form("true"),
    net_profit: str | None = Form(None),
    image: UploadFile | None = File(None),
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductItem:
    viewer = _user_by_email(db, user["email"])
    product = _load_product(db, product_id)
    if not _can_view(db, product, viewer):
        raise HTTPException(status_code=404, detail=_GENERIC)
    if not _can_pause(db, product, viewer):
        raise HTTPException(status_code=403, detail=_GENERIC)
    qty, amount = _parse_qty_price(quantity, price)
    ships_flag = _parse_flag(ships)
    pickup_flag = _parse_flag(pickup)
    if not ships_flag and not pickup_flag:
        raise HTTPException(status_code=422, detail="Los datos enviados no son válidos")
    product.name = name.strip()
    product.quantity = qty
    product.price = amount
    if net_profit is not None:
        product.net_profit = _parse_money(net_profit)
    product.category = category.strip()
    product.subcategory = subcategory.strip()
    product.ships = ships_flag
    product.pickup = pickup_flag
    if image is not None and image.filename:
        data = await _read_image(image)
        old_path = _image_file(product)
        product.image_path = _write_image(data)
        if old_path.is_file():
            old_path.unlink(missing_ok=True)
    db.commit()
    return _product_item(_load_product(db, product.id), include_profit=True)


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    viewer = _user_by_email(db, user["email"])
    product = _load_product(db, product_id)
    if not _can_view(db, product, viewer):
        raise HTTPException(status_code=404, detail=_GENERIC)
    if not _can_pause(db, product, viewer):
        raise HTTPException(status_code=403, detail=_GENERIC)
    question_ids = select(ProductQuestion.id).where(
        ProductQuestion.product_id == product.id
    )
    db.execute(delete(ProductAnswer).where(ProductAnswer.question_id.in_(question_ids)))
    db.execute(delete(ProductQuestion).where(ProductQuestion.product_id == product.id))
    db.execute(delete(Notification).where(Notification.product_id == product.id))
    image_path = _image_file(product)
    db.delete(product)
    db.commit()
    if image_path.is_file():
        image_path.unlink(missing_ok=True)
    return Response(status_code=204)


@router.get("/products/{product_id}/image")
def get_product_image(
    product_id: int,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    viewer = _user_by_email(db, user["email"])
    product = _load_product(db, product_id)
    if not _can_view(db, product, viewer):
        raise HTTPException(status_code=404, detail=_GENERIC)
    path = _image_file(product)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=_GENERIC)
    data = path.read_bytes()
    media = _media_type(data) or "application/octet-stream"
    return Response(content=data, media_type=media)


@router.post("/products/{product_id}/pause", response_model=ProductItem)
def pause_product(
    product_id: int,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductItem:
    viewer = _user_by_email(db, user["email"])
    product = _load_product(db, product_id)
    if not _can_pause(db, product, viewer):
        raise HTTPException(status_code=403, detail=_GENERIC)
    product.paused = True
    db.commit()
    return _product_item(_load_product(db, product.id), include_profit=True)


@router.post("/products/{product_id}/resume", response_model=ProductItem)
def resume_product(
    product_id: int,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductItem:
    viewer = _user_by_email(db, user["email"])
    product = _load_product(db, product_id)
    if not _can_pause(db, product, viewer):
        raise HTTPException(status_code=403, detail=_GENERIC)
    product.paused = False
    db.commit()
    return _product_item(_load_product(db, product.id), include_profit=True)


@router.post(
    "/products/{product_id}/questions",
    response_model=ProductQuestionItem,
    status_code=201,
)
async def create_question(
    product_id: int,
    payload: CreateQuestionRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductQuestionItem:
    viewer = _user_by_email(db, user["email"])
    product = _load_product(db, product_id)
    if not _can_view(db, product, viewer):
        raise HTTPException(status_code=404, detail=_GENERIC)
    if _can_pause(db, product, viewer):
        raise HTTPException(status_code=403, detail=_GENERIC)
    question = ProductQuestion(
        product_id=product.id,
        asker_user_id=viewer.id,
        text=payload.text.strip(),
        created_at=datetime.now(UTC),
    )
    db.add(question)
    db.flush()
    item = _question_item(question, None, reveal_email=False, asker=viewer)
    await emit_question(db, product, viewer, item.model_dump(mode="json"))
    return item


@router.post("/questions/{question_id}/answers", response_model=ProductQuestionItem)
async def create_answer(
    question_id: int,
    payload: CreateAnswerRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductQuestionItem:
    viewer = _user_by_email(db, user["email"])
    question = db.scalar(
        select(ProductQuestion).where(ProductQuestion.id == question_id)
    )
    if question is None:
        raise HTTPException(status_code=404, detail=_GENERIC)
    product = _load_product(db, question.product_id)
    if not _can_pause(db, product, viewer):
        raise HTTPException(status_code=403, detail=_GENERIC)
    answer = ProductAnswer(
        question_id=question.id,
        responder_user_id=viewer.id,
        text=payload.text.strip(),
        created_at=datetime.now(UTC),
    )
    db.add(answer)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo responder la pregunta",
        ) from None
    public_item = _question_item(question, answer.text, reveal_email=False)
    await emit_answer(
        db,
        product,
        viewer,
        question.asker_user_id,
        public_item.model_dump(mode="json"),
    )
    return _question_item(question, answer.text, reveal_email=True)
