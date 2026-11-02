from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.plain import PlainText


class ProductItem(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    id: int
    store_id: int
    store_name: str
    name: str
    quantity: int
    price: Decimal
    category: str
    subcategory: str
    paused: bool
    ships: bool
    pickup: bool
    net_profit: Decimal | None = None


class ProductListResponse(BaseModel):
    items: list[ProductItem]
    total: int
    page: int
    page_size: int


class ProductQuestionItem(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    id: int
    asker_label: str
    asker_email: str | None = None
    text: str
    answer: str | None = None


class ProductDetailResponse(ProductItem):
    questions: list[ProductQuestionItem]
    can_manage: bool


class CreateQuestionRequest(BaseModel):
    text: PlainText


class CreateAnswerRequest(BaseModel):
    text: PlainText
