from src.core.database import get_async_session
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.service import (
    create_user_and_send_verification_email,
    verify_email,
    login_user,
)
from .schemas import SignUpRequest, LoginRequest, BaseResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=BaseResponse)
async def signup(
    payload: SignUpRequest, session: AsyncSession = Depends(get_async_session)
):
    try:
        response = await create_user_and_send_verification_email(
            session, payload.name, payload.email, payload.password
        )
        return {"code": 200, "data": response}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify-email", response_model=BaseResponse)
async def verify_email_route(
    token: str, session: AsyncSession = Depends(get_async_session)
):
    response = await verify_email(session, token)
    return {"code": 200, "data": response}


@router.post("/login", response_model=BaseResponse)
async def login(
    payload: LoginRequest, session: AsyncSession = Depends(get_async_session)
):
    response = await login_user(session, payload.email, payload.password)
    return {"code": 200, "data": response}
