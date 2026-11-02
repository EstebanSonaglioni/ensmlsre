from decimal import Decimal

from pydantic import BaseModel

from app.schemas.plain import PlainText


class ProductItem(BaseModel):
    id: int
    store_id: int
    store_name: str
    seller_email: str
    name: str
    quantity: int
    price: Decimal
    net_profit: Decimal
    category: str
    subcategory: str
    paused: bool
    ships: bool
    pickup: bool


class ProductListResponse(BaseModel):
    items: list[ProductItem]
    total: int
    page: int
    page_size: int


class ProductQuestionItem(BaseModel):
    id: int
    asker_email: str
    text: str
    answer: str | None = None


class ProductDetailResponse(ProductItem):
    questions: list[ProductQuestionItem]
    can_manage: bool


class CreateQuestionRequest(BaseModel):
    text: PlainText


class CreateAnswerRequest(BaseModel):
    text: PlainText
