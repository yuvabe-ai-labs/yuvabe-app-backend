import uuid
from src.auth.utils import (
    # send_otp_email,
    verify_password,
    create_refresh_token,
    verify_verification_token,
    create_access_token,
    hash_password,
    create_verification_token,
)
from src.core.models import Users
from sqlmodel import Session, select
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession


async def create_user(session: AsyncSession, name: str, email: str, password: str):
    """Create user without sending email"""

    if not email.lower():
        raise HTTPException(status_code=400, detail="Enter you're Yuvabe email ID")

    user = await session.exec(select(Users).where(Users.email_id == email))
    existing_user = user.first()
    if existing_user:
        raise ValueError("User already exists")

    new_user = Users(
        user_name=name,
        email_id=email,
        password=hash_password(password),
        is_verified=True,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    access_token = create_access_token(
        data={
            "sub": str(new_user.id),
            "name": new_user.user_name,
            "email": new_user.email_id,
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(new_user.id),
            "name": new_user.user_name,
            "email": new_user.email_id,
        }
    )

    return {
        "message": "User created successfully",
        "user_id": str(new_user.id),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


# async def send_verification_link(session: Session, email: str):
#     """Send verification email for an existing user."""
#     result = await session.exec(select(Users).where(Users.email_id == email))
#     user = result.first()

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     if user.is_verified:
#         raise HTTPException(status_code=400, detail="User is already verified")

#     # Create a token using existing user ID (opaque token)
#     token = create_verification_token(str(user.id))

#     try:
#         send_verification_email(email, token)
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Failed to send verification email: {str(e)}"
#         )

#     return {
#         "message": "Verification link sent successfully",
#         "user_id": str(user.id),
#         "email": user.email_id,
#     }


async def verify_email(session: Session, token: str):
    try:
        user_id = await verify_verification_token(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = await session.get(Users, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_verified:
        user.is_verified = True
        await session.commit()

    access_token = create_access_token(
        data={"sub": str(user.id), "name": user.user_name, "email": user.email_id}
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "name": user.user_name, "email": user.email_id}
    )

    return {
        "message": "Email verified successfully!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def login_user(session: Session, email: str, password: str):

    if not email.lower():
        raise HTTPException(status_code=400, detail="Enter you're valid email ID")

    users = await session.exec(select(Users).where(Users.email_id == email))
    user = users.first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Verify email to login")

    access_token = create_access_token(
        data={"sub": str(user.id), "name": user.user_name, "email": user.email_id}
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "name": user.user_name, "email": user.email_id}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "name": user.user_name,
            "email": user.email_id,
            "is_verified": user.is_verified,
        },
    }
