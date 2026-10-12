import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_seller, get_db
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductImageResponse,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services import product as product_service



router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Public: anyone can browse products, one page at a time."""
    items, total = await product_service.list_products(db, page, page_size)
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)

# IMPORTANT: "/mine" must come BEFORE "/{product_id}", otherwise FastAPI would
# think "mine" is a product id and fail.
@router.get("/mine", response_model=ProductListResponse)
async def list_my_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    seller: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """Seller only: the seller's own products."""
    items, total = await product_service.list_products(db, page, page_size, seller.id)
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Public: one product with its images."""
    return await product_service.get_product(db, product_id)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    seller: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.create_product(db, seller, data)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    seller: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.update_product(db, product_id, seller, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    seller: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    await product_service.delete_product(db, product_id, seller)


@router.post(
    "/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    seller: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.add_image(db, product_id, seller, file)


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    seller: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    await product_service.delete_image(db, product_id, image_id, seller)