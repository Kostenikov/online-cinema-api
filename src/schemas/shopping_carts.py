from pydantic import BaseModel, ConfigDict


class CartItemResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    title: str
    price: float
    genres: list[str]
    release_year: int

    @classmethod
    def from_cart_item(cls, cart_item):
        movie = cart_item.movie
        return cls(
            id=cart_item.id,
            movie_id=cart_item.movie_id,
            title=movie.name,
            price=float(movie.price),
            genres=[g.name for g in movie.genres],
            release_year=movie.year,
        )


class CartResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    cart_items: list[CartItemResponseSchema] = []
