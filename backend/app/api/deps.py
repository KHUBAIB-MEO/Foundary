import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import async_session_maker
from app.models.user import User
from app.services.auth import get_user_by_id

# Tells FastAPI where to log in. This also adds the "Authorize" button in /docs.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")



async def get_db():
    """Give each request its own database session, then close it."""
    async with async_session_maker() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Find the logged-in user from the token in the request header."""
    error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token, "access")
    if payload is None:
        raise error
    user = await get_user_by_id(db, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise error
    return user


async def get_current_seller(user: User = Depends(get_current_user)) -> User:
    """Only sellers can pass."""
    if user.role != "seller":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sellers only")
    return user

async def get_current_customer(user: User = Depends(get_current_user)) -> User:
    """Only customers can pass."""
    if user.role != "customer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Customers only")
    return user