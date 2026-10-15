import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem
from app.models.user import User
from app.schemas.order import OrderItemResponse
from app.schemas.seller_order import SellerOrderResponse
from app.services import order as order_service

# new status -> the status the items must have right now
REQUIRED_PREVIOUS = {"confirmed": "pending", "shipped": "confirmed", "delivered": "shipped"}


def to_seller_response(order: Order, seller: User) -> SellerOrderResponse:
    """Show the seller only THEIR items of the order."""
    mine = [OrderItemResponse.model_validate(i) for i in order.items if i.seller_id == seller.id]
    return SellerOrderResponse(
        id=order.id,
        created_at=order.created_at,
        shipping_full_name=order.shipping_full_name,
        shipping_phone=order.shipping_phone,
        shipping_address=order.shipping_address,
        shipping_city=order.shipping_city,
        shipping_postal_code=order.shipping_postal_code,
        shipping_country=order.shipping_country,
        items=mine,
    )


async def list_seller_orders(
    db: AsyncSession, seller: User, page: int, page_size: int, item_status: str | None
) -> tuple[list[SellerOrderResponse], int]:
    """Paid orders that contain at least one item of this seller."""
    item_filters = [OrderItem.seller_id == seller.id]
    if item_status:
        item_filters.append(OrderItem.status == item_status)
    my_order_ids = select(OrderItem.order_id).where(*item_filters)

    conditions = [Order.payment_status == "paid", Order.id.in_(my_order_ids)]
    total = (await db.execute(select(func.count()).select_from(Order).where(*conditions))).scalar_one()
    query = (
        select(Order)
        .where(*conditions)
        .order_by(Order.created_at.desc(), Order.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .execution_options(populate_existing=True)
    )
    orders = (await db.execute(query)).scalars().all()
    return [to_seller_response(o, seller) for o in orders], total


async def update_status(
    db: AsyncSession, seller: User, order_id: uuid.UUID, new_status: str
) -> SellerOrderResponse:
    order = await order_service.get_order(db, order_id)
    my_items = [i for i in order.items if i.seller_id == seller.id]
    if not my_items:  # 404: do not reveal orders of other sellers
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    if order.payment_status != "paid":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This order is not paid yet")

    required = REQUIRED_PREVIOUS[new_status]
    active = [i for i in my_items if i.status != "cancelled"]
    if not active or any(i.status != required for i in active):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot change to '{new_status}': your items must be '{required}' first",
        )
    for item in active:
        item.status = new_status
    await db.commit()

    order = await order_service.get_order(db, order_id)
    return to_seller_response(order, seller)