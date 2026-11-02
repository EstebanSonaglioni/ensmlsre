from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SellMessage(Base):
    __tablename__ = "sell_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    sell_id: Mapped[int] = mapped_column(ForeignKey("sells.id"))
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
