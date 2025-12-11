# src/core/email_utils.py
import smtplib
from email.message import EmailMessage
from src.core.config import settings
from typing import List
import base64
import httpx
from typing import Dict, Optional
from src.core.config import settings
from urllib.parse import urlencode
from datetime import date
from typing import Tuple, Optional, List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.models import (
    UserTeamsRole,
    Roles,
    Users,
    Teams,
)  # adjust import path if differs
from src.core.config import settings  # for FCM key if needed
import httpx
from uuid import UUID
import uuid

def calculate_days(
    from_date: date, to_date: date, include_weekends: bool = True
) -> int:
    """Calculate inclusive days. If you want to exclude weekends, add logic."""
    delta = (to_date - from_date).days + 1
    return max(0, delta)

def safe_uuid(value):
    try:
        return uuid.UUID(str(value))
    except:
        return None



async def find_mentor_and_lead(
    session: AsyncSession, user_id
) -> Tuple[Optional[dict], Optional[dict]]:
    """
    Return (mentor_user, lead_user) as dicts or None.
    Uses your existing UserTeamsRole and Roles tables to find role members in same team.
    """
    # 1) find user's team mapping
    stmt = select(UserTeamsRole).where(UserTeamsRole.user_id == user_id)
    user_team = (await session.exec(stmt)).first()
    if not user_team:
        return None, None

    # 2) find Mentor role id
    mentor_role = (
        await session.exec(select(Roles).where(Roles.name == "Mentor"))
    ).first()
    lead_role = (
        await session.exec(select(Roles).where(Roles.name == "Team Lead"))
    ).first()

    mentor_user = None
    lead_user = None

    if mentor_role:
        mentor_user = (
            await session.exec(
                select(Users)
                .join(UserTeamsRole)
                .where(UserTeamsRole.team_id == user_team.team_id)
                .where(UserTeamsRole.role_id == mentor_role.id)
            )
        ).first()

    if lead_role:
        lead_user = (
            await session.exec(
                select(Users)
                .join(UserTeamsRole)
                .where(UserTeamsRole.team_id == user_team.team_id)
                .where(UserTeamsRole.role_id == lead_role.id)
            )
        ).first()

    return mentor_user, lead_user


async def get_tokens_for_user(session: AsyncSession, user_id) -> list[str]:
    user = await session.get(Users, user_id)
    if not user:
        return []
    return user.device_tokens or []


# Simple FCM send using legacy HTTP API (server key).
# In production prefer FCM HTTP v1 (OAuth) or firebase-admin SDK.
async def send_push_to_tokens(
    tokens: list[str], title: str, body: str, data: dict = None
):
    if not tokens:
        return

    server_key = getattr(settings, "FCM_SERVER_KEY", None)
    if not server_key:
        # no key configured: just log or skip
        print("FCM_SERVER_KEY not configured, skipping push")
        return

    url = "https://fcm.googleapis.com/fcm/send"
    headers = {
        "Authorization": f"key={server_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "registration_ids": tokens,
        "notification": {"title": title, "body": body},
    }
    if data:
        payload["data"] = data

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        # handle response in logs
        if r.status_code != 200:
            print("FCM send failed:", r.status_code, r.text)


SMTP_HOST = settings.EMAIL_SERVER
SMTP_PORT = settings.EMAIL_PORT
SMTP_USER = settings.EMAIL_USERNAME
SMTP_PASS = settings.EMAIL_PASSWORD
FROM_DEFAULT = settings.EMAIL_USERNAME

# src/utils/gmail_utils.py


def build_auth_url(state=None):
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.GMAIL_SEND_SCOPE + " openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    if state:
        params["state"] = state

    query = urlencode(params)
    return f"{settings.AUTH_BASE}?{query}"


async def exchange_code_for_tokens(code: str) -> Dict:
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(settings.TOKEN_URL, data=data)
        r.raise_for_status()
        return r.json()


async def refresh_access_token(refresh_token: str) -> Dict:
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(settings.TOKEN_URL, data=data)
        r.raise_for_status()
        return r.json()


def build_raw_message(
    to_email: str, subject: str, body: str, from_name: Optional[str], from_email: str
) -> str:

    msg = EmailMessage()
    sender = f"{from_name} <{from_email}>" if from_name else from_email
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    raw_bytes = msg.as_bytes()
    return base64.urlsafe_b64encode(raw_bytes).decode()


def send_email(
    to_email: str, subject: str, body: str, cc: list[str] = None, from_email: str = None
):
    """
    Gmail cannot send as another user.
    So we set 'From' = your Gmail, but 'Reply-To' = user email.
    """

    cc = cc or []

    msg = EmailMessage()
    msg["Subject"] = subject

    # Always send FROM your SMTP account
    msg["From"] = settings.EMAIL_USERNAME

    # Show this as reply address
    if from_email:
        msg["Reply-To"] = from_email

    msg["To"] = to_email

    if cc:
        msg["Cc"] = ", ".join(cc)

    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.EMAIL_SERVER, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)

            server.send_message(msg)

    except Exception as e:
        raise Exception(f"Email sending failed: {str(e)}")
