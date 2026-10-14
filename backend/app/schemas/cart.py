from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: UUID
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, le=100)


class CartProduct(BaseModel):
    """A short version of the product, just enough to show it in the cart."""
    id: UUID
    title: str
    price: Decimal
    stock: int
    image_url: str | None


class CartItemResponse(BaseModel):
    id: UUID
    product: CartProduct
    quantity: int
    line_total: Decimal  # price x quantity


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_quantity: int
    subtotal: Decimal