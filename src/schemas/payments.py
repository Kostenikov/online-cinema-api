from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer

from database import PaymentStatusEnum


class PaymentCreateSchema(BaseModel):
    order_id: int
    amount: Decimal


class PaymentItemResponseSchema(BaseModel):
    id: int
    order_item_id: int
    price_at_payment: Decimal

    @field_serializer("price_at_payment")
    def format_price(self, value: Decimal) -> float:
        return float(round(value, 2))


class PaymentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: Decimal
    status: PaymentStatusEnum
    external_payment_id: str | None
    external_payment_link: str | None
    created_at: datetime
    payment_items: list[PaymentItemResponseSchema] | None = None

    @field_serializer("amount")
    def format_amount(self, value: Decimal) -> float:
        return float(round(value, 2))


class PaymentOrderResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: PaymentStatusEnum
    external_payment_id: str | None
    external_payment_link: str | None
