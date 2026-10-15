from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.order import OrderResponse


class PaymentIntentResponse(BaseModel):
    """What the app needs to start paying (the same idea as a Stripe PaymentIntent)."""
    payment_id: UUID
    order_id: UUID
    provider: str
    amount: Decimal
    currency: str
    client_secret: str
    status: str


class MockPayRequest(BaseModel):
    """Simulates the customer typing a card. Only works with the mock provider."""
    payment_id: UUID
    card_number: str


class MockPayResponse(BaseModel):
    provider_status: str
    message: str


class PaymentConfirmResponse(BaseModel):
    status: str  # "succeeded", "failed" or "pending"
    message: str
    order: OrderResponse