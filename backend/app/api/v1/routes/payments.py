import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer, get_db
from app.models.user import User
from app.schemas.payment import (
    MockPayRequest,
    MockPayResponse,
    PaymentConfirmResponse,
    PaymentIntentResponse,
)
from app.services import payment as payment_service

router = APIRouter(tags=["Payments"])


@router.post("/orders/{order_id}/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    order_id: uuid.UUID,
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Step 1: start paying for an order."""
    return await payment_service.create_payment_intent(db, order_id, customer)


@router.post("/payments/mock/pay", response_model=MockPayResponse)
async def mock_pay(
    data: MockPayRequest,
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Step 2 (DEVELOPMENT ONLY): pretend to enter a card. 4242 4242 4242 4242 works."""
    return await payment_service.mock_pay(db, customer, data.payment_id, data.card_number)


@router.post("/orders/{order_id}/confirm-payment", response_model=PaymentConfirmResponse)
async def confirm_payment(
    order_id: uuid.UUID,
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Step 3: the server checks the payment with the provider and marks the order paid."""
    return await payment_service.confirm_payment(db, order_id, customer)