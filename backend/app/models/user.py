from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    display_name: Mapped[str] = mapped_column(String, default="")
    avatar_path: Mapped[str | None] = mapped_column(String, nullable=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
