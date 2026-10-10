from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse


router = APIRouter(prefix= "/user", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def read_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the logged-in user."""
    return current_user