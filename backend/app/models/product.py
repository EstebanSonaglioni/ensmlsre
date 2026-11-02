from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.store import Store
from app.models.user import User


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    net_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    category: Mapped[str] = mapped_column(String)
    subcategory: Mapped[str] = mapped_column(String)
    image_path: Mapped[str] = mapped_column(String)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    ships: Mapped[bool] = mapped_column(Boolean, default=True)
    pickup: Mapped[bool] = mapped_column(Boolean, default=True)

    store: Mapped[Store] = relationship()
    seller: Mapped[User] = relationship()


class ProductQuestion(Base):
    __tablename__ = "product_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    asker_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    product: Mapped[Product] = relationship()
    asker: Mapped[User] = relationship()


class ProductAnswer(Base):
    __tablename__ = "product_answers"
    __table_args__ = (UniqueConstraint("question_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("product_questions.id"))
    responder_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    question: Mapped[ProductQuestion] = relationship()
    responder: Mapped[User] = relationship()
