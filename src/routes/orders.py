from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import UserModel, get_db
from database.models.orders import OrderModel, OrderItemModel
from repository.orders import cancel_order, create_order_from_cart, get_user_orders
from schemas.orders import (
    OrderCreateResponseSchema,
    OrderItemResponseSchema,
    OrderResponseSchema,
)
from security.permissions import get_current_user, require_moderator

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
            id=order.id,
            user_id=order.user_id,
            created_at=order.created_at,
            total_amount=order.total_amount,
            status=order.status,
            order_items=[
                OrderItemResponseSchema(
                    id=item.id,
                    movie_id=item.movie_id,
                    title=item.movie.name,
                    price_at_order=item.price_at_order,
                )
                for item in order.order_items
            ],
        )
        for order in orders
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
        raise HTTPException(
            status_code=400,
            detail="Cannot create order: cart empty or no valid items.",
        )
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
    return OrderResponseSchema(
        id=order.id,
        user_id=order.user_id,
        created_at=order.created_at,
        total_amount=order.total_amount,
        status=order.status,
        order_items=[
            OrderItemResponseSchema(
                id=item.id,
                movie_id=item.movie_id,
                title=item.movie.name,
                price_at_order=item.price_at_order,
            )
            for item in order.order_items
        ],
    )


@router.get(
    "/admin/orders/",
    name="get_all_orders_admin",
    response_model=list[OrderResponseSchema],
    summary="Get all orders (admin only, optional filter by user_id)",
)
async def get_all_orders_admin(
    user_id: int | None = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_moderator),
):
    query = select(OrderModel).options(joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie)).order_by(OrderModel.created_at.desc())
    if user_id:
        query = query.filter(OrderModel.user_id == user_id)

    result = await db.execute(query)
    orders = result.scalars().unique().all()

    return [
        OrderResponseSchema(
            id=order.id,
            user_id=order.user_id,
            created_at=order.created_at,
            total_amount=order.total_amount,
            status=order.status,
            order_items=[
                OrderItemResponseSchema(
                    id=item.id,
                    movie_id=item.movie_id,
                    title=item.movie.name,
                    price_at_order=item.price_at_order,
                )
                for item in order.order_items
            ],
        )
        for order in orders
    ]
