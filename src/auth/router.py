from src.core.database import get_async_session
from fastapi import APIRouter, Depends, HTTPException, status

# from src.home.router import get_session
# from sqlmodel import Session
# from src.auth.service import login_user
from jose import jwt, JWTError
from src.auth.config import SECRET_KEY, ALGORITHM
from fastapi.security import OAuth2PasswordBearer

# from .schemas import SignUpRequest, VerifyOtpRequest, LoginRequest
# from .service import create_user_and_send_otp, verify_otp

# router = APIRouter(prefix="/auth", tags=["Auth"])


# @router.post("/signup")
# def signup(payload: SignUpRequest, session: Session = Depends(get_session)):
#     try:
#         return create_user_and_send_otp(
#             session, payload.name, payload.email, payload.password
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.post("/verify-otp")
# def verify_otp_route(
#     payload: VerifyOtpRequest, session: Session = Depends(get_session)
# ):
#     try:
#         return verify_otp(session, payload.email, payload.otp)
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.post("/login")
# def login(payload: LoginRequest, session: Session = Depends(get_session)):
#     return login_user(session, payload.email, payload.password)


from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from src.auth.service import (
    create_user_and_send_verification_email,
    verify_email,
    login_user,
)
from .schemas import SignUpRequest, LoginRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup")
async def signup(payload: SignUpRequest, session: Session = Depends(get_async_session)):
    try:
        return await create_user_and_send_verification_email(
            session, payload.name, payload.email, payload.password
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify-email")
async def verify_email_route(token: str, session: Session = Depends(get_async_session)):
    return await verify_email(session, token)


@router.post("/login")
async def login(payload: LoginRequest, session: Session = Depends(get_async_session)):
    return await login_user(session, payload.email, payload.password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
