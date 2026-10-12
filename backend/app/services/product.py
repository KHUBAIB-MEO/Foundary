import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.product import Product, ProductImage
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate
from app.services import storage




async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
    """Get one product (with its images) or raise 404."""
    # populate_existing = always re-read fresh values from the database.
    query = (
        select(Product).where (Product.id == product_id).execution_options(populate_existing=True)
    )  

    product = (await db.execute(query)).scalar_one_or_none()
    if product is None:
         raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


async def get_owned_product(db: AsyncSession, product_id: uuid.UUID, seller: User) -> Product:
    """Get a product and make sure it belongs to this seller."""
    product = await get_product(db, product_id)
    if product.seller_id != seller.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is not your product")
    return product

async def list_products(db: AsyncSession, page: int, page_size: int, seller_id: uuid.UUID | None = None) -> tuple[list[Product], int]:
    """Return one page of products (newest first) and the total number of products."""
    query = select(Product)
    count_query = select(func.count()).select_from(Product)

    if seller_id is not None:
        query = query.where(Product.seller_id == seller_id)
        count_query = count_query.where(Product.seller_id == seller_id)

    total = (await db.execute(count_query)).scalar_one()
    query = (
        query.order_by(Product.created_at.desc(), Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    products = (await db.execute(query)).scalars().all()
    return list(products), total

async def create_product(db: AsyncSession, seller: User, data: ProductCreate) -> Product:
    product = Product(seller_id=seller.id, **data.model_dump())
    db.add(product)
    await db.commit()
    return await get_product(db, product.id)


async def update_product(
    db: AsyncSession, product_id: uuid.UUID, seller: User, data: ProductUpdate
) -> Product:
    product = await get_owned_product(db, product_id, seller)
    # exclude_unset = only the fields the client really sent.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    return await get_product(db, product_id)

async def delete_product(db: AsyncSession, product_id: uuid.UUID, seller: User) -> None:
    product = await get_owned_product(db, product_id, seller)
    image_paths = [image.file_path for image in product.images]
    await db.delete(product)  # its image rows are deleted too (cascade)
    await db.commit()
    for path in image_paths:  # now remove the files from the disk
        storage.delete_file(path)

async def add_image(db: AsyncSession, product_id: uuid.UUID, seller: User, file: UploadFile) -> ProductImage:
    product = await get_owned_product(db, product_id, seller)
    if len(product.images) >= settings.MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"A product can have at most {settings.MAX_IMAGES_PER_PRODUCT} images",
        )

    relative_path, content_type = await storage.save_image(file)
    image = ProductImage(
        product_id=product.id,
        file_path=relative_path,
        file_name=Path(file.filename or "image").name[:200],
        file_type=content_type,
    )
    db.add(image)
    try:
        await db.commit()
    except Exception:
        storage.delete_file(relative_path)  # do not leave a file without a database row
        raise
    await db.refresh(image)
    return image


async def delete_image(
    db: AsyncSession, product_id: uuid.UUID, image_id: uuid.UUID, seller: User
) -> None:
    product = await get_owned_product(db, product_id, seller)
    image = next((img for img in product.images if img.id == image_id), None)
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    path = image.file_path
    await db.delete(image)
    await db.commit()
    storage.delete_file(path)

