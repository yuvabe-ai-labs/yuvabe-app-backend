# src/payslip/googleservice.py
import base64
import json
import requests
from fastapi import HTTPException
from src.core.config import settings

# TEMPORARY in-memory store
GOOGLE_TOKENS = {}  # user_id -> refresh_token


def exchange_code_for_tokens(code: str):
    """Exchange authorization code for access + refresh tokens."""
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    response = requests.post(settings.TOKEN_URL, data=data)
    return response.json()


def extract_email_from_id_token(id_token: str) -> str:
    """Decode ID token to extract the email Google selected."""
    try:
        payload_part = id_token.split(".")[1] + "==="
        decoded = json.loads(base64.urlsafe_b64decode(payload_part))
        return decoded.get("email")
    except Exception:
        raise HTTPException(400, "Invalid ID token format")


def refresh_google_access_token(refresh_token: str):
    """Refresh access token using refresh_token."""
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    response = requests.post(settings.TOKEN_URL, data=data)
    token_data = response.json()

    if "access_token" not in token_data:
        raise HTTPException(400, f"Google refresh failed: {token_data}")

    return token_data["access_token"]


def build_email(from_email: str, to_email: str, subject: str, body: str):
    """Build raw Gmail MIME email."""
    message = (
        f"From: {from_email}\r\n"
        f"To: {to_email}\r\n"
        f"Subject: {subject}\r\n\r\n"
        f"{body}"
    )
    return base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")


def send_gmail(access_token: str, raw_message: str):
    """Send email through Gmail API."""
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    data = {"raw": raw_message}

    res = requests.post(url, headers=headers, json=data)
    data = res.json()

    if "id" not in data:
        raise HTTPException(400, f"Gmail send error: {data}")

    return data["id"]
