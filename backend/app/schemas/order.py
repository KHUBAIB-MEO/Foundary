from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class CheckoutRequest(BaseModel):
    """The shipping address the customer types at checkout."""
    full_name: str = Field(..., min_length=1, max_length=150)
    phone: str = Field(..., min_length=7, max_length=30)
    address: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID | None
    seller_id: UUID
    product_title: str
    unit_price: Decimal
    quantity: int
    status: str

    @computed_field
    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    payment_status: str
    total_amount: Decimal
    shipping_full_name: str
    shipping_phone: str
    shipping_address: str
    shipping_city: str
    shipping_postal_code: str
    shipping_country: str
    created_at: datetime
    items: list[OrderItemResponse]


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int  