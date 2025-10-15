from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from database import PaymentStatusEnum


class PaymentCreateSchema(BaseModel):
    order_id: int
    amount: Decimal


class PaymentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: Decimal
    status: PaymentStatusEnum
    external_payment_id: str | None
    external_payment_link: str | None
    created_at: datetime
