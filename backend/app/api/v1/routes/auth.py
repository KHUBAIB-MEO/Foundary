from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.user import (
    EmailRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    TokenRequest,
    UserCreate,
    UserResponse,
)
from app.services import auth as auth_service
from app.services.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register/customer", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_customer(data: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user = await auth_service.create_user(db, data, role="customer")
    token = auth_service.create_verification_token(user)
    background_tasks.add_task(send_verification_email, user.email, token)
    return user

@router.post("/register/seller", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_seller(
    data: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    user = await auth_service.create_user(db, data, role="seller")
    token = auth_service.create_verification_token(user)
    background_tasks.add_task(send_verification_email, user.email, token)
    return user


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    # The form field is called "username" by the OAuth2 standard; we put the email in it.
    user = await auth_service.authenticate_user(db, form.username, form.password)
    return Token(access_token=auth_service.create_access_token(user))


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    data: EmailRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    user = await auth_service.get_user_by_email(db, data.email)
    if user and not user.is_verified:
        token = auth_service.create_verification_token(user)
        background_tasks.add_task(send_verification_email, user.email, token)
    # Always the same answer, so nobody can find out which emails are registered.
    return MessageResponse(message="If the account exists, a verification email was sent.")



@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: EmailRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user = await auth_service.get_user_by_email(db, data.email) 
    if user and user.is_active:
        token = auth_service.create_reset_token(user)
        background_tasks.add_task(send_password_reset_email, user.email, token)
    return MessageResponse(message="If the account exists, a reset email was sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(db, data.token, data.new_password)
    return MessageResponse(message="Password changed. You can log in now.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(data: TokenRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.verify_email(db, data.token)
    return MessageResponse(message="Email verified. You can log in now.")
