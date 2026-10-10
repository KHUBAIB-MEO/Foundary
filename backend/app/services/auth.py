import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate



async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)

async def create_user(db: AsyncSession, data: UserCreate, role: str) -> User:
    """Create a new user. The ROLE comes from our code, never from the client."""
    if await get_user_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=role,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """Check email + password. Raises an error if anything is wrong."""
    user = await get_user_by_email(db, email)
    # Same message for "no such email" and "wrong password" so attackers learn nothing.
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password or email", headers = {"WWW-Authenticate": "Bearer"},)
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is disabled")
    if not user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Please verify your email first")
    return user


def create_access_token(user: User) -> str:
    return create_token(str(user.id), "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_verification_token(user: User) -> str:
    return create_token(str(user.id), "verify", settings.VERIFY_TOKEN_EXPIRE_MINUTES)

def create_reset_token(user: User) -> str:
    # "fp" (fingerprint) = the end of the current password hash.
    # After the password changes, the hash changes, so this token stops working.
    return create_token(str(user.id), "reset", settings.RESET_TOKEN_EXPIRE_MINUTES, extra = {"fp" : user.hashed_password[-12:]},)

async def verify_email(db: AsyncSession, token:str) -> None:
    payload = decode_token(token, "verify")
    if payload is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired token")
    user = await get_user_by_id(db, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired token")
    user.is_verified = True
    await db.commit()


async def reset_password(db: AsyncSession, token: str, new_password: str)-> None:
    payload = decode_token(token, "reset")
    if payload is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired token")
    user = await get_user_by_id(db, uuid.UUID(payload["sub"]))
    # The token must match the CURRENT password, so it can only be used once.
    if user is None or payload.get("fp") != user.hashed_password[-12:]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired token")
    user.hashed_password = hash_password(new_password)
    await db.commit()

    
