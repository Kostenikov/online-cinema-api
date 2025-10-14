import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database import Base, OrderItemModel, OrderModel, UserModel


class PaymentStatusEnum(str, enum.Enum):
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    PENDING = "pending"


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum, name="payment_status_enum"),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    external_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", backref="payments")
    order: Mapped["OrderModel"] = relationship("OrderModel", backref="payments")
    payment_items: Mapped[list["PaymentItemModel"]] = relationship(
        "PaymentItemModel",
        back_populates="payment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentModel(id={self.id}, user_id={self.user_id}, order_id={self.order_id}, "
            f"amount={self.amount}, status='{self.status}', external_id={self.external_payment_id!r})>"
        )


class PaymentItemModel(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    price_at_payment: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    payment: Mapped["PaymentModel"] = relationship("PaymentModel", back_populates="payment_items")
    order_item: Mapped["OrderItemModel"] = relationship("OrderItemModel", backref="payment_items")

    def __repr__(self) -> str:
        return (
            f"<PaymentItemModel(id={self.id}, payment_id={self.payment_id}, "
            f"order_item_id={self.order_item_id}, price={self.price_at_payment})>"
        )
