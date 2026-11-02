from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

QuestionStatusFilter = Literal["pending", "answered", "all"]
QuestionSort = Literal["score", "wait", "net_profit", "created_at", "name"]
QuestionOrder = Literal["asc", "desc"]


class SellerQuestionItem(BaseModel):
    id: int
    product_id: int
    product_name: str
    text: str
    answer: str | None
    created_at: datetime
    wait_hours: Decimal
    net_profit: Decimal
    score: Decimal


class SellerQuestionListResponse(BaseModel):
    items: list[SellerQuestionItem]
    total: int
    page: int
    page_size: int
