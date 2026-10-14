import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import relationship

from app.db.base import Base

# Allowed values (we keep them as simple text in the database).
PAYMENT_STATUSES = ["unpaid", "paid", "cancelled"]
ITEM_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]


class Order(Base):
    __tablename__ = "orders"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    payment_status = Column(String(20), nullable=False, default="unpaid")
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Shipping address, typed by the customer at checkout and saved on the order.
    shipping_full_name = Column(String(150), nullable=False)
    shipping_phone = Column(String(30), nullable=False)
    shipping_address = Column(String(255), nullable=False)
    shipping_city = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    shipping_country = Column(String(100), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    order_id = Column(Uuid, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    # If the seller deletes the product later, the order item stays (product_id becomes NULL).
    product_id = Column(Uuid, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    seller_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)

    # A SNAPSHOT of the product at the time of purchase. If the seller changes the
    # title or price tomorrow, this old order must not change.
    product_title = Column(String(200), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Each seller moves THEIR items through these steps.
    status = Column(String(20), nullable=False, default="pending")

    order = relationship("Order", back_populates="items")