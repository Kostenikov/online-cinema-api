import stripe
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config.dependencies import get_settings
from database import get_db
from database.models.orders import OrderModel
from database.models.payments import PaymentModel, PaymentStatusEnum
from repository.payments import StripePaymentService
from schemas.payments import PaymentCreateSchema, PaymentResponseSchema
from security.permissions import get_current_user

settings = get_settings()

router = APIRouter()


@router.post("/create_test_payment/", response_model=PaymentResponseSchema)
async def create_test_payment(
    data: PaymentCreateSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await StripePaymentService().create_stripe_session(
        db=db,
        user_id=user.id,
        order_id=data.order_id,
        total_amount=data.amount,
    )


@router.post("/stripe_webhook/")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.SignatureVerificationError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

    try:
        if event["type"] == "checkout.session.completed":
            session_obj = event["data"]["object"]
            external_id = session_obj["id"]

            result = await db.execute(select(PaymentModel).where(PaymentModel.external_payment_id == external_id))
            payment = result.scalar_one_or_none()

            if payment:
                payment.status = PaymentStatusEnum.SUCCESSFUL
                order = await db.get(OrderModel, payment.order_id)
                if order:
                    order.status = "paid"  # TODO change order statuses
                await db.commit()

        elif event["type"] == "checkout.session.expired":
            session_obj = event["data"]["object"]
            external_id = session_obj["id"]

            result = await db.execute(select(PaymentModel).where(PaymentModel.external_payment_id == external_id))
            payment = result.scalar_one_or_none()

            if payment:
                payment.status = PaymentStatusEnum.CANCELED
                await db.commit()

        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
