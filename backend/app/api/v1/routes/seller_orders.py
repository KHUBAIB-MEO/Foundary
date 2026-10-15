import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_seller, get_db
from app.models.user import User
from app.schemas.seller_order import SellerOrderListResponse, SellerOrderResponse, SellerStatusUpdate
from app.services import seller_order as seller_order_service

router = APIRouter(prefix="/seller/orders", tags=["Seller Orders"])


@router.get("", response_model=SellerOrderListResponse)
async def list_seller_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    item_status: Literal["pending", "confirmed", "shipped", "delivered"] | None = Query(default=None),
    seller: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """Paid orders that contain my products. Optionally filter by status."""
    items, total = await seller_order_service.list_seller_orders(db, seller, page, page_size, item_status)
    return SellerOrderListResponse(items=items, total=total, page=page, page_size=page_size)


@router.patch("/{order_id}/status", response_model=SellerOrderResponse)
async def update_my_items_status(
    order_id: uuid.UUID,
    data: SellerStatusUpdate,
    seller: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """Move my items of this order forward: pending, confirmed, shipped, delivered."""
    return await seller_order_service.update_status(db, seller, order_id, data.status)