from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserModel, get_db
from repository.orders import cancel_order, create_order_from_cart, get_user_orders
from schemas.orders import (
    OrderCreateResponseSchema,
    OrderResponseSchema,
)
from security.permissions import get_current_user

router = APIRouter()


@router.get(
    "/orders/",
    name="get_user_orders",
    response_model=list[OrderResponseSchema],
    summary="Get all user orders",
)
async def get_orders(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orders = await get_user_orders(db, user.id)
    return [
        OrderResponseSchema(
            id=o.id,
            user_id=o.user_id,
            created_at=o.created_at,
            total_amount=o.total_amount,
            status=o.status,
            order_items=[
                {
                    "id": item.id,
                    "movie_id": item.movie_id,
                    "title": item.movie.name,
                    "price_at_order": item.price_at_order,
                }
                for item in o.order_items
            ],
        )
        for o in orders
    ]


@router.post(
    "/orders/create/",
    name="create_order_from_cart",
    response_model=OrderCreateResponseSchema,
    summary="Create order from cart",
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order, excluded = await create_order_from_cart(db, user.id)
    if not order:
        raise HTTPException(status_code=400, detail="Cannot create order: cart empty or no valid items.")
    return OrderCreateResponseSchema(
        message="Order created successfully.",
        order_id=order.id,
        excluded_items=excluded if excluded else [],
    )


@router.post(
    "/orders/{order_id}/cancel/",
    name="cancel_order",
    response_model=OrderResponseSchema,
    summary="Cancel pending order",
)
async def cancel_order_route(
    order_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order, error = await cancel_order(db, order_id, user.id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return order
