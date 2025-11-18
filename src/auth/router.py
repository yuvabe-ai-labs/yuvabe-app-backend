import uuid
from src.core.database import get_async_session
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.service import (
    create_user,
    verify_email,
    login_user,
)
from src.auth.utils import get_current_user
from src.core.models import Users
from src.core.config import settings
from fastapi.responses import RedirectResponse
from .schemas import SignUpRequest, LoginRequest, BaseResponse, SendVerificationRequest
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.utils import create_access_token
from jose import jwt, JWTError


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=BaseResponse)
async def signup(
    payload: SignUpRequest, session: AsyncSession = Depends(get_async_session)
):
    try:
        response = await create_user(
            session, payload.name, payload.email, payload.password
        )
        return {"code": 200, "data": response}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# @router.post("/send-verification", response_model=BaseResponse)
# async def send_verification(
#     payload: SendVerificationRequest, session: AsyncSession = Depends(get_async_session)
# ):
#     if not payload.email:
#         raise HTTPException(status_code=400, detail="Email is required")

#     response = await send_verification_link(session, payload.email)
#     return {"code": 200, "data": response}


# @router.get("/verify-email", response_model=BaseResponse)
# async def verify_email_route(
#     token: str, session: AsyncSession = Depends(get_async_session)
# ):
#     response = await verify_email(session, token)
#     access_token = response["access_token"]
#     redirect_url = f"yuvabe://verified?token={access_token}"

#     return RedirectResponse(url=redirect_url)


@router.post("/login", response_model=BaseResponse)
async def login(
    payload: LoginRequest, session: AsyncSession = Depends(get_async_session)
):
    response = await login_user(session, payload.email, payload.password)
    return {"code": 200, "data": response}


@router.post("/refresh", response_model=BaseResponse)
async def refresh_token(request: dict):
    """Generate new access token using refresh token"""
    refresh_token = request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token is required")

    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid refresh token")

        user_data = {
            "sub": payload["sub"],
            "name": payload.get("name"),
            "email": payload.get("email"),
        }
        new_access_token = create_access_token(data=user_data)
        return {"code": 200, "data": {"access_token": new_access_token}}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.get("/home", response_model=BaseResponse)
async def get_home(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Protected home endpoint. Requires a valid access token (Bearer).
    """
    user = await session.get(Users, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Example payload — replace with your real app data
    return {
        "code": 200,
        "data": {
            "message": f"Welcome to Home, {user.user_name}!",
            "user": {
                "id": str(user.id),
                "name": user.user_name,
                "email": user.email_id,
                "is_verified": user.is_verified,
                "dob": user.dob.isoformat() if user.dob else None,
                "profile_picture": user.profile_picture
            },
            "home_data": {
                "announcements": ["Welcome!", "New protocol released"],
                "timestamp": user.created_at.isoformat() if user.created_at else None,
            },
        },
    }
