import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer, get_db
from app.models.user import User
from app.schemas.order import CheckoutRequest, OrderListResponse, OrderResponse
from app.services import order as order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    data: CheckoutRequest,
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Turn the cart into an order. Needs the shipping address."""
    return await order_service.checkout(db, customer, data)


@router.get("", response_model=OrderListResponse)
async def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    items, total = await order_service.list_orders(db, customer, page, page_size)
    return OrderListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_my_order(
    order_id: uuid.UUID,
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.get_customer_order(db, order_id, customer)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_my_order(
    order_id: uuid.UUID,
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an unpaid order. The stock goes back to the products."""
    return await order_service.cancel_order(db, order_id, customer)