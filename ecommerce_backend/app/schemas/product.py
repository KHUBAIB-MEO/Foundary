from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime

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

