from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import User


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)


class StoreMembership(Base):
    __tablename__ = "store_memberships"
    __table_args__ = (UniqueConstraint("store_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String)

    store: Mapped[Store] = relationship()
    user: Mapped[User] = relationship()


class StoreInvitation(Base):
    __tablename__ = "store_invitations"
    __table_args__ = (UniqueConstraint("store_id", "email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    email: Mapped[str] = mapped_column(String)

    store: Mapped[Store] = relationship()
