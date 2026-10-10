from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    """What the client sends to register. Note: there is NO role here."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=150)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_verified: bool 
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenRequest(BaseModel):
    """Used for verify-email (the token from the email)."""
    token: str

class EmailRequest(BaseModel):
    """Used for resend-verification and forgot-password."""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

class MessageResponse(BaseModel):
    message: str

