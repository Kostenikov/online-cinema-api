from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, UserModel, CartItemModel, OrderItemModel, OrderModel
from repository import get_shopping_cart, create_shopping_cart
from schemas import CartResponseSchema
from fastapi import APIRouter, Depends, status, HTTPException
from security.permissions import get_current_user
from sqlalchemy import select, delete

router = APIRouter()


@router.get(
    "/cart/",
    name="get_cart",
    response_model=CartResponseSchema,
    summary="Get shopping cart",
    status_code=status.HTTP_200_OK,
)
async def get_cart(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartResponseSchema:
    cart = await get_shopping_cart(db, user.id)
    if not cart:
        cart = await create_shopping_cart(db, user.id)
    return cart


@router.post(
    "/cart/items/",
    name="add_item_to_cart",
    response_model=CartResponseSchema,
    summary="Add item to cart",
    status_code=status.HTTP_200_OK,
)
async def add_item(
    item_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartResponseSchema:
    cart = await get_shopping_cart(db, user.id)
    if not cart:
        cart = await create_shopping_cart(db, user.id)
        return cart

    item_exists = await db.scalar(
        select(CartItemModel).where(
            CartItemModel.cart_id == cart.id,
            CartItemModel.movie_id == item_id,
        )
    )
    if item_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item already in your cart.",
        )

    item_purchased = await db.scalar(
        select(OrderItemModel.movie_id)
        .join(OrderModel)
        .where(
            OrderModel.user_id == user.id,
            OrderItemModel.movie_id == item_id,
        )
    )
    if item_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already purchased this item.",
        )

    cart_item = CartItemModel(cart_id=cart.id, movie_id=item_id)
    db.add(cart_item)
    await db.commit()
    await db.refresh(cart)
    return cart


@router.delete(
    "/cart/items/{item_id}/",
    name="remove_item_from_cart",
    response_model=CartResponseSchema,
    summary="Remove item from cart",
    status_code=status.HTTP_200_OK,
)
async def remove_item(
    item_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartResponseSchema:
    cart = await get_shopping_cart(db, user.id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart does not exist.",
        )

    item = await db.scalar(
        select(CartItemModel)
        .where(
            CartItemModel.id == item_id,
            CartItemModel.cart_id == cart.id,
        )
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item does not exist.",
        )

    await db.delete(item)
    await db.commit()
    await db.refresh(item)
    return cart


@router.delete(
    "/cart/clear/",
    name="clear_cart",
    summary="Clear shopping cart",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_cart(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_shopping_cart(db, user.id)
    if not cart:
        cart = await create_shopping_cart(db, user.id)
    else:
        await db.execute(
            delete(CartItemModel)
            .where(
                CartItemModel.cart_id == cart.id,
            )
        )
        await db.commit()
