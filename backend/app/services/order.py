import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import CheckoutRequest


async def get_order(db: AsyncSession, order_id: uuid.UUID) -> Order:
    query = select(Order).where(Order.id == order_id).execution_options(populate_existing=True)
    order = (await db.execute(query)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


async def get_customer_order(db: AsyncSession, order_id: uuid.UUID, customer: User) -> Order:
    order = await get_order(db, order_id)
    # 404 (not 403): do not reveal that someone else's order exists.
    if order.customer_id != customer.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


async def list_orders(
    db: AsyncSession, customer: User, page: int, page_size: int
) -> tuple[list[Order], int]:
    total = (
        await db.execute(select(func.count()).select_from(Order).where(Order.customer_id == customer.id))
    ).scalar_one()
    query = (
        select(Order)
        .where(Order.customer_id == customer.id)
        .order_by(Order.created_at.desc(), Order.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list((await db.execute(query)).scalars().all()), total


async def _lock_product(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    """Read a product AND lock its row until we commit.

    If two customers buy the last item at the same moment, the second one waits
    here until the first one is finished, then sees the real, updated stock.
    """
    query = (
        select(Product)
        .where(Product.id == product_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return (await db.execute(query)).scalar_one_or_none()


async def checkout(db: AsyncSession, customer: User, data: CheckoutRequest) -> Order:
    """Turn the customer's cart into an order."""
    # Sorted by product id: every checkout locks products in the same order,
    # which prevents two checkouts from blocking each other forever (deadlock).
    query = select(CartItem).where(CartItem.user_id == customer.id).order_by(CartItem.product_id)
    cart_items = list((await db.execute(query)).scalars().all())
    if not cart_items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Your cart is empty")

    order = Order(
        customer_id=customer.id,
        total_amount=Decimal("0"),
        shipping_full_name=data.full_name,
        shipping_phone=data.phone,
        shipping_address=data.address,
        shipping_city=data.city,
        shipping_postal_code=data.postal_code,
        shipping_country=data.country,
    )
    total = Decimal("0")

    for cart_item in cart_items:
        product = await _lock_product(db, cart_item.product_id)
        if product is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "A product in your cart no longer exists")
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Not enough stock for '{product.title}' (available: {product.stock})",
            )
        product.stock -= cart_item.quantity  # reserve the stock for this order
        order.items.append(
            OrderItem(
                product_id=product.id,
                seller_id=product.seller_id,
                product_title=product.title,  # snapshot
                unit_price=product.price,  # snapshot
                quantity=cart_item.quantity,
            )
        )
        total += product.price * cart_item.quantity

    order.total_amount = total
    db.add(order)
    await db.execute(delete(CartItem).where(CartItem.user_id == customer.id))
    await db.commit()  # order + stock changes + empty cart are saved TOGETHER, or not at all
    return await get_order(db, order.id)


async def cancel_order(db: AsyncSession, order_id: uuid.UUID, customer: User) -> Order:
    order = await get_customer_order(db, order_id, customer)
    if order.payment_status != "unpaid":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Only unpaid orders can be cancelled"
        )
    for item in sorted(order.items, key=lambda i: str(i.product_id)):
        if item.product_id is not None:  # give the stock back
            product = await _lock_product(db, item.product_id)
            if product is not None:
                product.stock += item.quantity
        item.status = "cancelled"
    order.payment_status = "cancelled"
    await db.commit()
    return await get_order(db, order_id)