import uuid
import smtplib
from email.mime.text import MIMEText
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from src.auth.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import secrets
from datetime import datetime, timedelta
import os
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "Hariprasath137@gmail.com"
SMTP_PASSWORD = "jdtc qyaq fmqd xvse"


def send_otp_email(to_email: str, otp: str):
    subject = "Your Yuvabe OTP Code"
    body = f"Your OTP is {otp}. It will expire in 5 minutes."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_opaque_token():
    return secrets.token_urlsafe(32)


# def send_verification_email(to_email: str, token: str):
#     subject = "Verify your Yuvabe Account"
#     verification_link = (
#         f"https://68c71e06225c.ngrok-free.app/auth/verify-email?token={token}"
#     )
#     body = f"""
#     Hi,

#     Please click the link below to verify your email address:
#     {verification_link}

#     This link will expire in 24 hours.
#     """

#     msg = MIMEText(body)
#     msg["Subject"] = subject
#     msg["From"] = SMTP_EMAIL
#     msg["To"] = to_email


#     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#         server.starttls()
#         server.login(SMTP_EMAIL, SMTP_PASSWORD)
#         server.send_message(msg)


def send_verification_email(to_email: str, token: str):
    subject = "Verify your Yuvabe Account"
    verification_link = (
        f"https://68c71e06225c.ngrok-free.app/auth/verify-email?token={token}"
    )
    body = f"""
    Hi,

    Please verify your Yuvabe account by clicking the link below:
    {verification_link}

    This link will expire in 24 hours.
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)


FERNET_KEY = os.getenv("FERNET_KEY")
fernet = Fernet(FERNET_KEY)


def create_verification_token(user_id: str, expires_in_hours: int = 24) -> str:
    """Create an encrypted verification token containing the user_id and expiry time."""
    payload = {
        "sub": user_id,
        "exp": (datetime.utcnow() + timedelta(hours=expires_in_hours)).timestamp(),
    }
    token = fernet.encrypt(json.dumps(payload).encode()).decode()
    return token


async def verify_verification_token(token: str) -> str:
    """Verify and decrypt a verification token, returning the user_id if valid."""
    try:
        decrypted = fernet.decrypt(token.encode())
        data = json.loads(decrypted.decode())

        exp = datetime.fromtimestamp(data["exp"])
        if datetime.utcnow() > exp:
            raise ValueError("Verification link expired")

        return data["sub"]

    except InvalidToken:
        raise ValueError("Invalid verification link")
