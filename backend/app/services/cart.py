import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemResponse, CartProduct, CartResponse


async def get_cart_items(db: AsyncSession, user: User) -> list[CartItem]:
    query = (
        select(CartItem)
        .where(CartItem.user_id == user.id)
        .order_by(CartItem.created_at, CartItem.id)
        .execution_options(populate_existing=True)
    )
    return list((await db.execute(query)).scalars().all())


def build_cart_response(items: list[CartItem]) -> CartResponse:
    """Turn database rows into what the app needs, and calculate the totals."""
    response_items = []
    for item in items:
        product = item.product
        image_url = f"/uploads/{product.images[0].file_path}" if product.images else None
        response_items.append(
            CartItemResponse(
                id=item.id,
                product=CartProduct(
                    id=product.id,
                    title=product.title,
                    price=product.price,
                    stock=product.stock,
                    image_url=image_url,
                ),
                quantity=item.quantity,
                line_total=product.price * item.quantity,
            )
        )
    return CartResponse(
        items=response_items,
        total_quantity=sum(i.quantity for i in items),
        subtotal=sum((i.line_total for i in response_items), Decimal("0")),
    )


async def get_cart(db: AsyncSession, user: User) -> CartResponse:
    return build_cart_response(await get_cart_items(db, user))


def _check_stock(product: Product, wanted: int) -> None:
    if wanted > product.stock:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Only {product.stock} of '{product.title}' in stock",
        )


async def add_item(db: AsyncSession, user: User, product_id: uuid.UUID, quantity: int) -> CartResponse:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")

    query = select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    item = (await db.execute(query)).scalar_one_or_none()

    if item is None:
        _check_stock(product, quantity)
        db.add(CartItem(user_id=user.id, product_id=product_id, quantity=quantity))
    else:  # already in the cart: increase the quantity
        _check_stock(product, item.quantity + quantity)
        item.quantity += quantity
    await db.commit()
    return await get_cart(db, user)


async def _get_own_item(db: AsyncSession, user: User, item_id: uuid.UUID) -> CartItem:
    item = await db.get(CartItem, item_id)
    # 404 (not 403) so nobody can find out which ids exist in other people's carts.
    if item is None or item.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cart item not found")
    return item


async def set_quantity(db: AsyncSession, user: User, item_id: uuid.UUID, quantity: int) -> CartResponse:
    item = await _get_own_item(db, user, item_id)
    _check_stock(item.product, quantity)
    item.quantity = quantity
    await db.commit()
    return await get_cart(db, user)


async def remove_item(db: AsyncSession, user: User, item_id: uuid.UUID) -> CartResponse:
    item = await _get_own_item(db, user, item_id)
    await db.delete(item)
    await db.commit()
    return await get_cart(db, user)


async def clear_cart(db: AsyncSession, user: User) -> None:
    await db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    await db.commit()