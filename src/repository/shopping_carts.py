from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import CartModel


async def get_shopping_cart(db: AsyncSession, user_id: int) -> CartModel:
    cart = await db.scalar(
        select(CartModel).options(joinedload(CartModel.cart_items)).where(CartModel.user_id == user_id)
    )
    return cart


async def create_shopping_cart(db: AsyncSession, user_id: int) -> CartModel:
    cart = CartModel(user_id=user_id)
    db.add(cart)
    await db.commit()
    await db.refresh(cart)
    return cart
