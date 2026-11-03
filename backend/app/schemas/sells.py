from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.plain import require_plain

Fulfillment = Literal["envio", "retiro"]
PaymentMethod = Literal["tarjeta", "transferencia", "efectivo"]
SellStatus = Literal[
    "en_carrito",
    "en_curso",
    "en_viaje",
    "esperando_retiro",
    "completada",
    "cancelada",
    "reembolsada",
]


class CreateSellRequest(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    fulfillment: Fulfillment


class PatchSellRequest(BaseModel):
    quantity: int | None = Field(default=None, ge=1)
    fulfillment: Fulfillment | None = None


class CheckoutItem(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    fulfillment: Fulfillment


class CheckoutRequest(BaseModel):
    payment_method: PaymentMethod
    sell_ids: list[int] | None = None
    items: list[CheckoutItem] | None = None


class TransitionRequest(BaseModel):
    status: SellStatus


class CreateMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=1000)

    @field_validator("body")
    @classmethod
    def reject_html(cls, value: str) -> str:
        return require_plain(value)


class SellMessageItem(BaseModel):
    id: int
    sell_id: int
    sender_user_id: int
    body: str
    created_at: datetime
    mine: bool = False


class SellMessageListResponse(BaseModel):
    items: list[SellMessageItem]
    total: int
    page: int
    page_size: int


class NotificationItem(BaseModel):
    id: int
    sell_id: int | None = None
    product_id: int | None = None
    kind: Literal["mensaje", "estado", "pregunta", "respuesta", "venta"]
    title: str
    body: str
    as_seller: bool = False
    read_at: datetime | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    total: int
    unread: int
    page: int
    page_size: int


class SellItem(BaseModel):
    id: int
    product_id: int
    product_name: str
    store_name: str
    buyer_email: str
    seller_email: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    fulfillment: Fulfillment
    payment_method: PaymentMethod | None = None
    status: SellStatus
    checkout_id: str | None = None
    eta_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    can_manage: bool = False


class SellListResponse(BaseModel):
    items: list[SellItem]
    total: int
    page: int
    page_size: int
