import secrets
import uuid
from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException, status

from app.core.config import settings
from app.models.payment import Payment


@dataclass
class ProviderPayment:
    """What a provider gives us when a payment is created."""
    provider_payment_id: str
    client_secret: str


@dataclass
class ProviderStatus:
    """What a provider tells us about a payment."""
    status: str  # "pending", "succeeded" or "failed"
    failure_reason: str | None = None


# Test cards, copied from how Stripe's own test cards behave.
MOCK_CARDS = {
    "4242424242424242": None,  # works
    "4000000000000002": "Your card was declined.",
    "4000000000009995": "Your card has insufficient funds.",
}


class MockPaymentProvider:
    """A fake payment company that behaves like Stripe, for development."""

    name = "mock"

    def create_payment(self, amount: Decimal, currency: str) -> ProviderPayment:
        payment_id = f"pi_mock_{uuid.uuid4().hex[:20]}"
        return ProviderPayment(
            provider_payment_id=payment_id,
            client_secret=f"{payment_id}_secret_{secrets.token_hex(8)}",
        )

    def get_status(self, payment: Payment) -> ProviderStatus:
        """With real Stripe this would ask Stripe's servers. Here we read our own column."""
        if payment.provider_status == "succeeded":
            return ProviderStatus("succeeded")
        if payment.provider_status == "failed":
            return ProviderStatus("failed", payment.failure_reason)
        return ProviderStatus("pending")

    def pay(self, payment: Payment, card_number: str) -> None:
        """Pretend the customer's phone paid with a card. Real Stripe does this on the phone."""
        card = card_number.replace(" ", "")
        if card in MOCK_CARDS and MOCK_CARDS[card] is None:
            payment.provider_status = "succeeded"
            payment.failure_reason = None
        else:
            payment.provider_status = "failed"
            payment.failure_reason = MOCK_CARDS.get(card, "Invalid card number.")


_mock_provider = MockPaymentProvider()


def get_provider() -> MockPaymentProvider:
    if settings.PAYMENT_PROVIDER == "mock":
        return _mock_provider
    raise HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        f"Unknown payment provider '{settings.PAYMENT_PROVIDER}'",
    )