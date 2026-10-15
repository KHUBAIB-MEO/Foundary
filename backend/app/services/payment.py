import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import MockPayResponse, PaymentConfirmResponse, PaymentIntentResponse
from app.services import order as order_service
from app.services.payment_providers import get_provider


def _to_intent_response(payment: Payment) -> PaymentIntentResponse:
    return PaymentIntentResponse(
        payment_id=payment.id,
        order_id=payment.order_id,
        provider=payment.provider,
        amount=payment.amount,
        currency=payment.currency,
        client_secret=payment.client_secret,
        status=payment.status,
    )


async def _latest_payment(db: AsyncSession, order_id: uuid.UUID) -> Payment | None:
    query = (
        select(Payment)
        .where(Payment.order_id == order_id)
        .order_by(Payment.created_at.desc(), Payment.id)
        .limit(1)
        .execution_options(populate_existing=True)
    )
    return (await db.execute(query)).scalar_one_or_none()


async def create_payment_intent(
    db: AsyncSession, order_id: uuid.UUID, customer: User
) -> PaymentIntentResponse:
    order = await order_service.get_customer_order(db, order_id, customer)
    if order.payment_status == "paid":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This order is already paid")
    if order.payment_status == "cancelled":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This order was cancelled")

    # If a payment is already waiting, give the same one back (no duplicates).
    latest = await _latest_payment(db, order.id)
    if latest is not None and latest.status == "pending":
        return _to_intent_response(latest)

    provider = get_provider()
    created = provider.create_payment(order.total_amount, settings.PAYMENT_CURRENCY)
    payment = Payment(
        order_id=order.id,
        provider=provider.name,
        provider_payment_id=created.provider_payment_id,
        client_secret=created.client_secret,
        amount=order.total_amount,  # the server decides the amount, never the client
        currency=settings.PAYMENT_CURRENCY,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return _to_intent_response(payment)


async def mock_pay(
    db: AsyncSession, customer: User, payment_id: uuid.UUID, card_number: str
) -> MockPayResponse:
    """Development only: simulates the customer paying with a test card."""
    if settings.PAYMENT_PROVIDER != "mock":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    payment = await db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    await order_service.get_customer_order(db, payment.order_id, customer)  # must be yours
    if payment.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"This payment is already {payment.status}")

    get_provider().pay(payment, card_number)
    await db.commit()
    if payment.provider_status == "succeeded":
        return MockPayResponse(
            provider_status="succeeded", message="Card accepted. Now call confirm-payment."
        )
    return MockPayResponse(
        provider_status="failed",
        message=f"{payment.failure_reason} Call confirm-payment to record it.",
    )


async def confirm_payment(
    db: AsyncSession, order_id: uuid.UUID, customer: User
) -> PaymentConfirmResponse:
    """The app says 'I paid'. We do NOT believe it: we ask the provider."""
    # Lock the order row so two confirm calls at the same time cannot clash.
    lock_query = (
        select(Order).where(Order.id == order_id).with_for_update().execution_options(populate_existing=True)
    )
    order = (await db.execute(lock_query)).scalar_one_or_none()
    if order is None or order.customer_id != customer.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")

    if order.payment_status == "paid":  # calling confirm twice is harmless
        return PaymentConfirmResponse(status="succeeded", message="Order is already paid", order=order)
    if order.payment_status == "cancelled":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This order was cancelled")

    payment = await _latest_payment(db, order.id)
    if payment is None or payment.status != "pending":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "No payment in progress. Start one with payment-intent first"
        )

    result = get_provider().get_status(payment)
    if result.status == "succeeded":
        payment.status = "succeeded"
        order.payment_status = "paid"
        await db.commit()
        message = "Payment received. Thank you!"
    elif result.status == "failed":
        payment.status = "failed"
        payment.failure_reason = result.failure_reason
        await db.commit()
        message = f"Payment failed: {result.failure_reason} You can try again with a new payment-intent."
    else:
        message = "Payment not completed yet."

    order = await order_service.get_order(db, order_id)
    return PaymentConfirmResponse(status=result.status, message=message, order=order)