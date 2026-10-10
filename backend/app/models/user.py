import uuid
from sqlalchemy import Boolean, Column, DateTime, String, Uuid, false, func
from app.db.base import Base


class User(Base):

    __tablename__ = "users"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(255), default="customer", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable = True, server_default=false())
    created_at = Column(DateTime(timezone=True), server_default=func.now())