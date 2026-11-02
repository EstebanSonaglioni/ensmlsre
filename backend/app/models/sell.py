from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.product import Product
from app.models.user import User


class Sell(Base):
    __tablename__ = "sells"

    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    store_id: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fulfillment: Mapped[str] = mapped_column(String)
    payment_method: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    checkout_id: Mapped[str | None] = mapped_column(String, nullable=True)
    eta_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    product: Mapped[Product] = relationship()
    buyer: Mapped[User] = relationship(foreign_keys=[buyer_user_id])
    seller: Mapped[User] = relationship(foreign_keys=[seller_user_id])
