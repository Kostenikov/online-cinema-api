from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import CartItemModel, CartModel, OrderItemModel, OrderModel


async def get_user_orders(db: AsyncSession, user_id: int):
    result = await db.scalars(
        select(OrderModel)
        .options(selectinload(OrderModel.order_items).selectinload(OrderItemModel.movie))
        .where(OrderModel.user_id == user_id)
        .order_by(OrderModel.created_at.desc())
    )
    return result.all()


async def create_order_from_cart(db: AsyncSession, user_id: int):
    cart = await db.scalar(
        select(CartModel)
        .options(selectinload(CartModel.cart_items).selectinload(CartItemModel.movie))
        .where(CartModel.user_id == user_id)
    )
    if not cart or not cart.cart_items:
        return None, "Cart is empty."

    available_items = []
    excluded_items = []

    for item in cart.cart_items:
        movie = item.movie
        if not movie:
            excluded_items.append("Unknown movie")
        else:
            available_items.append(item)

    if not available_items:
        return None, f"All movies unavailable: {excluded_items}"

    total_amount = sum((Decimal(item.movie.price) for item in available_items), Decimal(0))

    new_order = OrderModel(
        user_id=user_id,
        status="pending",
        total_amount=total_amount,
    )
    db.add(new_order)
    await db.flush()

    for item in available_items:
        order_item = OrderItemModel(
            order_id=new_order.id,
            movie_id=item.movie_id,
            price_at_order=item.movie.price,
        )
        db.add(order_item)

    for item in available_items:
        await db.delete(item)

    await db.commit()
    await db.refresh(new_order)
    return new_order, excluded_items


async def cancel_order(db: AsyncSession, order_id: int, user_id: int):
    order = await db.scalar(
        select(OrderModel)
        .options(joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie))
        .where(OrderModel.id == order_id)
    )
    if not order:
        return None, "Order not found."
    if order.status != "pending":
        return None, "Only pending orders can be canceled."

    order.status = "canceled"
    await db.commit()
    await db.refresh(order)
    return order, None
