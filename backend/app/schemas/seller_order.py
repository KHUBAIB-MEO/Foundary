from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, computed_field

from app.schemas.order import OrderItemResponse


class SellerStatusUpdate(BaseModel):
    # A seller can only move forward. Cancelling is not part of this phase.
    status: Literal["confirmed", "shipped", "delivered"]


class SellerOrderResponse(BaseModel):
    """An order as a SELLER sees it: only their own items, plus where to ship."""
    id: UUID
    created_at: datetime
    shipping_full_name: str
    shipping_phone: str
    shipping_address: str
    shipping_city: str
    shipping_postal_code: str
    shipping_country: str
    items: list[OrderItemResponse]

    @computed_field
    @property
    def seller_total(self) -> Decimal:
        return sum((item.line_total for item in self.items), Decimal("0"))


class SellerOrderListResponse(BaseModel):
    items: list[SellerOrderResponse]
    total: int
    page: int
    page_size: int