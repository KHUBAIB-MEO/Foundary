import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, Uuid, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    # One row per (user, product). Adding the same product again increases quantity.
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_items_user_product"),)
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Load the product together with the cart item (needed in async code).
    product = relationship("Product", lazy="selectin")