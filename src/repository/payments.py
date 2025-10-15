from abc import ABC, abstractmethod

import stripe
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.dependencies import get_settings
from database import PaymentModel, PaymentStatusEnum

settings = get_settings()


class BasePaymentService(ABC):
    """
    Basic payment service with abstract methods
    for future payment services
    """

    @abstractmethod
    def create_stripe_session(self, db: AsyncSession, user_id: int, order_id: int, amount: float):
        pass


class StripePaymentService(BasePaymentService):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            stripe.api_key = settings.STRIPE_SECRET_KEY
        return cls._instance

    async def create_stripe_session(self, db: AsyncSession, user_id: int, order_id: int, amount: float):
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": f"Order #{order_id}"},
                            "unit_amount": int(amount * 100),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=f"{settings.DOMAIN}/api/v1/payments/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.DOMAIN}/api/v1/payments/cancel",
            )

            payment = PaymentModel(
                user_id=user_id,
                order_id=order_id,
                amount=amount,
                external_payment_id=session.id,
                external_payment_link=session.url,
                status=PaymentStatusEnum.PENDING,
            )
            db.add(payment)
            await db.commit()

            return payment

        except stripe.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
