from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DashboardProductItem(BaseModel):
    product_id: int
    name: str
    units: int
    amount: Decimal
    net_profit: Decimal


class DashboardSellerItem(BaseModel):
    email: str
    sales_count: int
    amount: Decimal


class NetProfitDay(BaseModel):
    date: date
    amount: Decimal
    net_profit: Decimal
    cumulative: Decimal


class OpenByStatus(BaseModel):
    en_curso: int = 0
    en_viaje: int = 0
    esperando_retiro: int = 0


class MixSlice(BaseModel):
    key: str
    count: int
    amount: Decimal


class DashboardPrevious(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: datetime = Field(serialization_alias="from")
    sales_count: int
    total_amount: Decimal
    net_profit_total: Decimal
    units_sold: int
    average_ticket: Decimal
    cancelled_count: int


class DashboardDelta(BaseModel):
    sales_count_pct: Decimal | None = None
    total_amount_pct: Decimal | None = None
    net_profit_total_pct: Decimal | None = None
    units_sold_pct: Decimal | None = None
    average_ticket_pct: Decimal | None = None
    cancelled_count_pct: Decimal | None = None


class DashboardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    days: int
    from_: datetime = Field(serialization_alias="from")
    sales_count: int
    total_amount: Decimal
    net_profit_total: Decimal
    units_sold: int
    average_ticket: Decimal
    open_orders: int
    cancelled_count: int
    refunded_count: int
    refunded_amount: Decimal
    top_products: list[DashboardProductItem]
    sellers: list[DashboardSellerItem]
    net_profit_series: list[NetProfitDay]
    open_by_status: OpenByStatus
    fulfillment_mix: list[MixSlice]
    payment_mix: list[MixSlice]
    previous: DashboardPrevious
    delta: DashboardDelta
