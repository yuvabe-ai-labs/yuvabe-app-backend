import uuid
from src.auth.utils import (
    # send_otp_email,
    verify_password,
    verify_verification_token,
    create_access_token,
    hash_password,
    send_verification_email,
    create_verification_token,
)
from src.core.models import Users
from sqlmodel import Session, select
from fastapi import HTTPException


async def create_user_and_send_verification_email(
    session: Session, name: str, email: str, password: str
):
    user = await session.exec(select(Users).where(Users.email_id == email))
    existing_user = user.first()
    if existing_user:
        raise ValueError("User already exists")

    new_user = Users(
        user_name=name,
        email_id=email,
        password=hash_password(password),
        is_verified=False,
    )
    session.add(new_user)

    # Create encrypted token using Fernet
    token = create_verification_token(str(new_user.id))
    

    # Send email
    send_verification_email(email, token)
    await session.commit()

    return {"message": "Verification email sent. Please check your inbox."}


async def verify_email(session: Session, token: str):
    try:
        user_id = await verify_verification_token(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = await session.get(Users, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    await session.commit()

    return {"message": "Email verified successfully!"}


async def login_user(session: Session, email: str, password: str):
    users = await session.exec(select(Users).where(Users.email_id == email))
    user = users.first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(
            status_code=403, detail="Please verify your email before logging in"
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "name": user.user_name, "email": user.email_id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "name": user.user_name,
            "email": user.email_id,
        },
    }
