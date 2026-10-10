from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    """Turn '12345678' into a long scrambled text we can safely store."""
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a typed password matches the stored hash."""
    return password_hash.verify(plain_password, hashed_password)

def create_token(subject: str, purpose: str, expires_minutes: int, extra: dict | None = None) -> str:
    """Create a signed token (JWT).

    subject  = who the token is for (the user id)
    purpose  = what the token may be used for: "access", "verify" or "reset"
    """

    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

    payload = {"sub" : subject, "purpose" : purpose, "exp" : expire}

    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str, purpose: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    if payload.get("purpose") != purpose:
        return None
    return payload