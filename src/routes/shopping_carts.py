from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, UserModel, CartModel
from schemas import CartResponseSchema
from fastapi import APIRouter, Depends, status
from security.permissions import get_current_user
from sqlalchemy import select
router = APIRouter()


@router.get(
    "/cart/",
    name="get_cart",
    response_model=CartResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_cart(
        user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> CartResponseSchema:
    cart = await db.scalar(
        select(CartModel)
        .options(
            joinedload(CartModel.cart_items)
        )
        .where(CartModel.user_id == user.id)
    )
    if not cart:
        cart = CartModel(user_id=user.id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    return cart


@router.post(
    "/cart/items/",
    name="add_item_to_cart",
    response_model=CartResponseSchema,
    summary="Add item to cart",
    status_code=status.HTTP_200_OK,
)
async def add_item(
        user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> CartResponseSchema:
    cart = await db.scalar(
        select(CartModel)
        .options(
            joinedload(CartModel.cart_items)
        )
        .where(CartModel.user_id == user.id)
    )
    if not cart:
        cart = CartModel(user_id=user.id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    return cart
