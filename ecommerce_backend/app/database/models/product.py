import uuid

from datetime import datetime, timezone
from app.database.base import Base
from sqlalchemy import Column, String, Text, ForeignKey, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable = False)
    description = Column(Text, nullable = True)
    title = Column(Text, nullable = False)
    price = Column(Numeric(10, 2), nullable = False)
    image_url = Column(String(500), nullable = False)
    file_type = Column(String(100), nullable = False)
    file_name = Column(String(200), nullable = False)
    stock = Column(Integer, nullable = False, default = 0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),onupdate=lambda: datetime.now(timezone.utc))

    