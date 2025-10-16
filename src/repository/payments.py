from abc import ABC, abstractmethod

import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.dependencies import get_settings
from database import OrderItemModel, PaymentItemModel, PaymentModel, PaymentStatusEnum

settings = get_settings()


class BasePaymentService(ABC):
    """
    Basic payment service with abstract methods
    for future payment services
    """

    @abstractmethod
    def create_stripe_session(
        self, db: AsyncSession, user_id: int, order_id: int, order_items: list[OrderItemModel], total_amount: float
    ):
        pass


class StripePaymentService(BasePaymentService):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            stripe.api_key = settings.STRIPE_SECRET_KEY
        return cls._instance

    async def create_stripe_session(
        self,
        db: AsyncSession,
        user_id: int,
        order_id: int,
        order_items: list[OrderItemModel],
        total_amount: float,
    ):
        try:
            line_items = [
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{item.movie.name}",
                            "description": f"Movie id: {item.movie_id}",
                        },
                        "unit_amount": int(item.movie.price * 100),
                    },
                    "quantity": 1,
                }
                for item in order_items
            ]

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=f"{settings.DOMAIN}/api/v1/orders/",
                cancel_url=f"{settings.DOMAIN}/api/v1/payments/cancel",
            )

            payment = PaymentModel(
                user_id=user_id,
                order_id=order_id,
                amount=total_amount,
                external_payment_id=session.id,
                external_payment_link=session.url,
                status=PaymentStatusEnum.PENDING,
            )
            db.add(payment)
            await db.commit()

            for item in order_items:
                payment_item = PaymentItemModel(
                    payment_id=payment.id,
                    order_item_id=order_id,
                    price_at_payment=item.movie.price,
                )
                db.add(payment_item)

            await db.commit()

            return payment

        except stripe.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")


async def get_user_payments(db: AsyncSession, user_id: int):
    """Get all user payments"""
    result = await db.scalars(
        select(PaymentModel)
        .options(selectinload(PaymentModel.payment_items).selectinload(PaymentItemModel.order_item))
        .where(PaymentModel.user_id == user_id)
        .order_by(PaymentModel.created_at.desc())
    )
    return result.all()
