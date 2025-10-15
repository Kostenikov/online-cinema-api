from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import CartItemModel, MovieModel, OrderItemModel, OrderModel, UserModel, get_db, CartModel
from repository import create_shopping_cart, get_shopping_cart
from schemas import CartItemResponseSchema, CartResponseSchema, MessageResponseSchema
from security.permissions import get_current_user, require_moderator

router = APIRouter()


@router.get(
    "/",
    name="moderator_get_carts",
    response_model=list[CartResponseSchema],
    summary="Get shopping all carts of users",
    status_code=status.HTTP_200_OK,
)
async def get_carts(
    current_user: Annotated[UserModel, Depends(require_moderator)],
    db: AsyncSession = Depends(get_db),

) -> list[CartResponseSchema]:
    """
    Fetch the shopping carts of all users for moderator.

    Args:
        current_user (UserModel): The current moderator user.
        db (AsyncSession): The database session.

    Returns:
        list[CartResponseSchema]: The shopping cart data, including items if any.
    """
    res = await db.scalars(
        select(CartModel)
        .options(
            selectinload(CartModel.cart_items)
            .selectinload(CartItemModel.movie)
            .selectinload(MovieModel.genres)
        )
    )
    carts = res.all()

    return [
        CartResponseSchema(
            id=cart.id,
            user_id=cart.user_id,
            cart_items=[CartItemResponseSchema.from_cart_item(item) for item in cart.cart_items],
        )
        for cart in carts
    ]


@router.get(
    "/cart/",
    name="get_cart",
    response_model=CartResponseSchema,
    summary="Get shopping cart",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Cart retrieved successfully."},
    },
)
async def get_cart(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartResponseSchema:
    """
    Fetch the shopping cart for the authenticated user.

    If the user has no existing cart, a new empty cart will be created automatically.

    Args:
        user (UserModel): The currently authenticated user.
        db (AsyncSession): The database session.

    Returns:
        CartResponseSchema: The shopping cart data, including items if any.
    """
    cart = await get_shopping_cart(db, user.id)
    if not cart:
        cart = await create_shopping_cart(db, user.id)
        return CartResponseSchema(id=cart.id, user_id=cart.user_id, cart_items=[])
    return CartResponseSchema(
        id=cart.id,
        user_id=cart.user_id,
        cart_items=[CartItemResponseSchema.from_cart_item(item) for item in cart.cart_items],
    )


@router.post(
    "/cart/items/",
    name="add_item_to_cart",
    response_model=MessageResponseSchema,
    summary="Add item to cart",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Item added to cart successfully."},
        400: {"description": "Item already exists in cart or already purchased."},
        404: {"description": "Item not found."},
    },
)
async def add_item(
    item_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a movie to the user's shopping cart.

    Validations:
    - Item must exist in the database.
    - Item must not already be in the cart.
    - Item must not have been already purchased by the user.

    Args:
        item_id (int): The ID of the movie to add.
        user (UserModel): The currently authenticated user.
        db (AsyncSession): The database session.

    Returns:
        MessageResponseSchema: Confirmation message of the operation.
    """
    cart = await get_shopping_cart(db, user.id)
    if not cart:
        cart = await create_shopping_cart(db, user.id)

    item_exists = await db.get(MovieModel, item_id)
    if not item_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item does not exist",
        )

    item_in_cart = await db.scalar(
        select(CartItemModel).where(
            CartItemModel.cart_id == cart.id,
            CartItemModel.movie_id == item_id,
        )
    )
    if item_in_cart:
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
    return MessageResponseSchema(
        message="Item added to your cart successfully.",
    )


@router.delete(
    "/cart/items/{item_id}/",
    name="remove_item_from_cart",
    response_model=MessageResponseSchema,
    summary="Remove item from cart",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Item removed from cart."},
        404: {"description": "No items with this id found."},
    },
)
async def remove_item(
    item_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a specific item from the user's shopping cart.

    Args:
        item_id (int): The ID of the item to remove.
        user (UserModel): The currently authenticated user.
        db (AsyncSession): The database session.

    Returns:
        MessageResponseSchema: Confirmation message of the operation.
    """
    cart = await get_shopping_cart(db, user.id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart does not exist.",
        )

    item = await db.scalar(
        select(CartItemModel).where(
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
    await db.refresh(cart)
    return MessageResponseSchema(
        message="Item removed from your cart successfully.",
    )


@router.delete(
    "/cart/clear/",
    name="clear_cart",
    summary="Clear shopping cart",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Cart cleared successfully."},
    },
)
async def clear_cart(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove all items from the user's shopping cart.
    If the user has no cart, a new empty cart will be created automatically.

    Args:
        user (UserModel): The currently authenticated user.
        db (AsyncSession): The database session.

    Returns:
        None
    """
    cart = await get_shopping_cart(db, user.id)
    if not cart:
        cart = await create_shopping_cart(db, user.id)
    else:
        await db.execute(
            delete(CartItemModel).where(
                CartItemModel.cart_id == cart.id,
            )
        )
        await db.commit()
