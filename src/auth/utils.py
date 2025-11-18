import json
import smtplib
import os
import uuid
from email.mime.text import MIMEText
import logging
import traceback
from passlib.context import CryptContext
from src.core.database import get_async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, status
from src.core.models import Users
from src.core.config import settings


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRE
logger = logging.getLogger(__name__)

SMTP_SERVER = settings.EMAIL_SERVER
SMTP_PORT = settings.EMAIL_PORT
SMTP_EMAIL = settings.EMAIL_USERNAME
SMTP_PASSWORD = settings.EMAIL_PASSWORD

FERNET_KEY = settings.FERNET_KEY
VERIFICATION_BASE_URL = settings.VERIFICATION_BASE_URL


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Encrypt plain password into hashed password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare plain password with stored hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    """Create JWT token with expiry"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# def send_verification_email(to_email: str, token: str):
#     """Send verification email using smtplib with detailed debug logs."""
#     subject = f"Verify your {settings.APP_NAME} Account"
#     verification_link = f"{VERIFICATION_BASE_URL}/auth/verify-email?token={token}"

#     body = f"""
#     Hi,

#     Please verify your {settings.APP_NAME} account by clicking the link below:
#     {verification_link}

#     This link will expire in 24 hours.

#     Regards,
#     {settings.APP_NAME} Team
#     """

#     msg = MIMEText(body)
#     msg["Subject"] = subject
#     msg["From"] = SMTP_EMAIL
#     msg["To"] = to_email

#     logger.info("🟢 Starting send_verification_email()")
#     logger.info(f"📨 To: {to_email}")
#     logger.info(f"📤 SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")

#     try:
#         logger.info("🔌 Connecting to SMTP server...")
#         with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
#             logger.info("✅ Connected successfully.")

#             logger.info("🔒 Starting TLS...")
#             server.starttls()
#             logger.info("✅ TLS secured.")

#             logger.info("🔑 Logging in to SMTP server...")
#             server.login(SMTP_EMAIL, SMTP_PASSWORD)
#             logger.info("✅ Logged in successfully.")

#             # Send email
#             logger.info("📧 Sending email message...")
#             server.send_message(msg)
#             logger.info(f"✅ Email successfully sent to {to_email}")

#     except smtplib.SMTPAuthenticationError as e:
#         logger.error("❌ Authentication failed — check email or app password.")
#         logger.error(f"Error details: {e}")
#         logger.error(traceback.format_exc())
#         raise
#     except smtplib.SMTPConnectError as e:
#         logger.error("❌ Could not connect to SMTP server.")
#         logger.error(f"Error details: {e}")
#         logger.error(traceback.format_exc())
#         raise
#     except smtplib.SMTPRecipientsRefused as e:
#         logger.error("❌ Recipient address refused.")
#         logger.error(f"Error details: {e}")
#         logger.error(traceback.format_exc())
#         raise
#     except smtplib.SMTPException as e:
#         logger.error("❌ General SMTP error occurred.")
#         logger.error(f"Error details: {e}")
#         logger.error(traceback.format_exc())
#         raise
#     except Exception as e:
#         logger.error("❌ Unknown error occurred while sending verification email.")
#         logger.error(f"Error details: {e}")
#         logger.error(traceback.format_exc())
#         raise


fernet = Fernet(FERNET_KEY.encode())


def create_verification_token(user_id: str, expires_in_hours: int = 24) -> str:
    """Create encrypted token with expiry"""
    payload = {
        "sub": user_id,
        "exp": (datetime.utcnow() + timedelta(hours=expires_in_hours)).timestamp(),
    }
    token = fernet.encrypt(json.dumps(payload).encode()).decode()
    return token


async def verify_verification_token(token: str) -> str:
    """Verify encrypted token and extract user_id"""
    try:
        decrypted = fernet.decrypt(token.encode())
        data = json.loads(decrypted.decode())

        exp = datetime.fromtimestamp(data["exp"])
        if datetime.utcnow() > exp:
            raise ValueError("Verification link expired")

        return data["sub"]

    except InvalidToken:
        raise ValueError("Invalid verification link")


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """Decode JWT token and extract current user ID"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user id",
            )
        return user_id

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_active_user(
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
) -> Users:
    """Return the full user model for the currently authenticated user."""
    user = await session.get(Users, uuid.UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User not verified"
        )
    return user


def create_refresh_token(data: dict, expires_days: int = 7):
    """Create a long-lived JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=expires_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
