from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

class ProductCreate(BaseModel):

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    price: Decimal = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)



class ProductUpdate(BaseModel): 
    title: str | None = Field(default = None, min_length=1, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(default = None, gt=0) 
    stock: int | None = Field(default = None, ge=0)


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_path: str
    file_name: str
    file_type: str
    created_at: datetime 

    @computed_field
    @property
    def url(self) -> str:
        """The address the app uses to show the image, e.g. /uploads/products/abc.jpg"""
        return f"/uploads/{self.file_path}"

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seller_id: UUID
    title: str
    description: str | None
    price: Decimal
    stock: int
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageResponse] = []


class ProductListResponse(BaseModel):
    """One page of products plus the numbers the app needs to build 'next page'."""
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int