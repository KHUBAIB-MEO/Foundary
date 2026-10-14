import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_customer, get_db
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from app.services import cart as cart_service

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse)
async def get_cart(customer: User = Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    return await cart_service.get_cart(db, customer)


@router.post("/items", response_model=CartResponse)
async def add_to_cart(
    data: CartItemAdd,
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await cart_service.add_item(db, customer, data.product_id, data.quantity)


@router.patch("/items/{item_id}", response_model=CartResponse)
async def change_quantity(
    item_id: uuid.UUID,
    data: CartItemUpdate,
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await cart_service.set_quantity(db, customer, item_id, data.quantity)


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_from_cart(
    item_id: uuid.UUID,
    customer: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await cart_service.remove_item(db, customer, item_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(customer: User = Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    await cart_service.clear_cart(db, customer)