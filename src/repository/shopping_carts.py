from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import CartItemModel, CartModel, MovieModel


async def get_shopping_cart(db: AsyncSession, user_id: int) -> CartModel:
    return await db.scalar(
        select(CartModel)
        .options(selectinload(CartModel.cart_items).selectinload(CartItemModel.movie).selectinload(MovieModel.genres))
        .where(CartModel.user_id == user_id)
    )


async def create_shopping_cart(db: AsyncSession, user_id: int) -> CartModel:
    cart = CartModel(user_id=user_id)
    db.add(cart)
    await db.commit()
    await db.refresh(cart, attribute_names=["cart_items"])
    return cart
