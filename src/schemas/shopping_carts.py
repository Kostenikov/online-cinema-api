from pydantic import BaseModel, ConfigDict
from datetime import date


class CartItemBaseSchema(BaseModel):
    movie_id: int


class CartItemCreateSchema(CartItemBaseSchema):
    pass


class CartItemResponseSchema(CartItemBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    title: str
    price: float
    genre: str
    release_year: date


class CartBaseScheme(BaseModel):
    id: int
    user_id: int


class CartResponseSchema(CartBaseScheme):
    model_config = ConfigDict(from_attributes=True)

    cart_items: list[CartItemResponseSchema]
