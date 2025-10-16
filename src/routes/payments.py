import stripe
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from config.dependencies import get_settings
from database import OrderStatusEnum, UserModel, get_db
from database.models.orders import OrderModel
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatusEnum
from repository.payments import StripePaymentService, get_user_payments
from schemas.payments import PaymentCreateSchema, PaymentResponseSchema
from security.permissions import get_current_user, require_moderator

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
                    order.status = OrderStatusEnum.PAID
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


@router.get(
    "/",
    name="get_user_payments",
    response_model=list[PaymentResponseSchema],
    summary="Get all payments for current user",
)
async def get_payments(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payments = await get_user_payments(db, user.id)
    return [payment for payment in payments]


@router.get(
    "/for_staff/",
    name="get_all_payments_admin",
    response_model=list[PaymentResponseSchema],
    summary="Get all payments (admin only, optional filter by user_id)",
)
async def get_all_payments_admin(
    user_id: int | None = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_moderator),
):
    query = (
        select(PaymentModel)
        .options(joinedload(PaymentModel.payment_items).joinedload(PaymentItemModel.order_item))
        .order_by(PaymentModel.created_at.desc())
    )
    if user_id:
        query = query.filter(PaymentModel.user_id == user_id)

    result = await db.execute(query)
    payments = result.scalars().unique().all()

    return [payment for payment in payments]
