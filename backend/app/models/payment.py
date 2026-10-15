import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Uuid, func

from app.db.base import Base

# Our own view of a payment attempt.
PAYMENT_ATTEMPT_STATUSES = ["pending", "succeeded", "failed", "cancelled"]


class Payment(Base):
    """One payment ATTEMPT for an order. An order can have several (e.g. first card declined)."""

    __tablename__ = "payments"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    order_id = Column(Uuid, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(30), nullable=False)  # "mock" or "stripe"
    provider_payment_id = Column(String(100), nullable=False, unique=True)
    client_secret = Column(String(200), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    failure_reason = Column(String(255), nullable=True)

    provider_status = Column(String(30), nullable=False, default="requires_payment_method")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())