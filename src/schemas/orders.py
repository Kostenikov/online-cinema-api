from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class OrderItemResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    title: str
    price_at_order: Decimal

    @classmethod
    def from_order_item(cls, order_item):
        return cls(
            id=order_item.id,
            movie_id=order_item.movie_id,
            title=order_item.movie.name,
            price_at_order=order_item.price_at_order,
        )


class OrderResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    total_amount: Decimal
    status: str
    order_items: list[OrderItemResponseSchema] = []


class OrderCreateResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    order_id: int | None = None
    excluded_items: list[str] = []
