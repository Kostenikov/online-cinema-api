from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database import Base, MovieModel, UserModel


class OrderStatusEnum(str, Enum):
    pending = "pending"
    paid = "paid"
    canceled = "canceled"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="orders",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OrderStatusEnum.pending.value,
    )

    total_amount: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    order_items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<OrderModel(id={self.id}, user_id={self.user_id}, " f"status={self.status}, total={self.total_amount})>"
        )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    order: Mapped[OrderModel] = relationship(
        "OrderModel",
        back_populates="order_items",
    )

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id"),
        nullable=False,
    )
    movie: Mapped[MovieModel] = relationship(
        "MovieModel",
        back_populates="order_items",
    )

    price_at_order: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<OrderItemModel(id={self.id}, order_id={self.order_id}, "
            f"movie_id={self.movie_id}, price={self.price_at_order})>"
        )
