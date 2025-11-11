import uuid
import random

from datetime import datetime
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


def generate_otp():
    return str(random.randint(100000, 999999))


# def create_user_and_send_otp(session: Session, name: str, email: str, password: str):
#     # 1. If already verified user exists, block new registration
#     existing_user = session.exec(select(Users).where(Users.email_id == email)).first()
#     if existing_user:
#         raise ValueError("User already exists")

#     otp = generate_otp()
#     expires_at = datetime.now() + timedelta(minutes=5)

#     existing_otp = session.exec(
#         select(OtpVerification).where(OtpVerification.email == email)
#     ).first()

#     if existing_otp:
#         session.delete(existing_otp)
#         session.commit()

#     new_otp = OtpVerification(
#         email=email,
#         otp=otp,
#         expires_at=expires_at,
#         temp_name=name,
#         temp_password=password,
#     )
#     session.add(new_otp)
#     session.commit()
#     send_otp_email(email, otp)

#     return {"message": "OTP sent successfully"}


# def create_user_and_send_verification_email(
#     session: Session, name: str, email: str, password: str
# ):
#     existing_user = session.exec(select(Users).where(Users.email_id == email)).first()
#     if existing_user:
#         raise ValueError("User already exists")

#     # Create secure token
#     token = generate_opaque_token()
#     expires_at = datetime.utcnow() + timedelta(hours=24)

#     # Create user
#     new_user = Users(
#         user_name=name,
#         email_id=email,
#         password=hash_password(password),
#         is_verified=False,
#         verification_token=token,
#         verification_expires_at=expires_at,
#     )
#     session.add(new_user)
#     session.commit()

#     # Send verification email
#     send_verification_email(email, token)

#     return {"message": "Verification email sent. Please check your inbox."}


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
    await session.commit()

    # Create encrypted token using Fernet
    token = create_verification_token(str(new_user.id))

    # Send email
    send_verification_email(email, token)

    return {"message": "Verification email sent. Please check your inbox."}


# def verify_email(session: Session, token: str):
#     user = session.exec(select(Users).where(Users.verification_token == token)).first()

#     if not user:
#         raise HTTPException(status_code=400, detail="Invalid or expired token")

#     if user.verification_expires_at < datetime.utcnow():
#         raise HTTPException(status_code=400, detail="Verification link expired")

#     user.is_verified = True
#     user.verification_token = None
#     user.verification_expires_at = None
#     session.commit()

#     return {"message": "Email verified successfully!"}


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


# def verify_otp(session: Session, email: str, otp: str):
#     record = session.exec(
#         select(OtpVerification).where(OtpVerification.email == email)
#     ).first()

#     if not record:
#         raise ValueError("No OTP record found")
#     if record.is_verified:
#         return {"message": "Email already verified"}
#     if record.expires_at < datetime.now():
#         raise ValueError("OTP expired")
#     if record.otp != otp:
#         raise ValueError("Invalid OTP")

#     new_user = Users(
#         user_name=record.temp_name,
#         email_id=email,
#         password=hash_password(record.temp_password),
#     )
#     session.add(new_user)

#     record.is_verified = True
#     session.commit()

#     return {"message": "Email verified successfully. Account created!"}


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
