import base64
import json
import requests
from typing import Tuple
from fastapi import HTTPException

from src.core.config import settings


def exchange_code_for_tokens(code: str):
    """
    Exchange Google 'code' for access_token + refresh_token
    """
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    res = requests.post(settings.TOKEN_URL, data=data)
    if res.status_code != 200:
        raise HTTPException(500, f"Google token exchange error: {res.text}")

    return res.json()


def refresh_google_access_token(refresh_token: str) -> str:
    """
    Input → refresh_token  
    Output → new access_token
    """
    data = {
        "refresh_token": refresh_token,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }

    res = requests.post(settings.TOKEN_URL, data=data)
    if res.status_code != 200:
        raise HTTPException(500, f"Failed to refresh access token: {res.text}")

    return res.json()["access_token"]


def build_email(from_email: str, to_email: str, subject: str, body: str) -> str:
    """
    Gmail API expects Base64URL-encoded email.
    """
    message = (
        f"From: {from_email}\r\n"
        f"To: {to_email}\r\n"
        f"Subject: {subject}\r\n"
        "\r\n"
        f"{body}"
    )

    message_bytes = message.encode("utf-8")
    encoded = base64.urlsafe_b64encode(message_bytes).decode("utf-8")
    return encoded


def send_gmail(access_token: str, raw_message: str) -> str:
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {"raw": raw_message}

    res = requests.post(url, headers=headers, data=json.dumps(payload))

    if res.status_code not in (200, 202):
        raise HTTPException(500, f"Gmail API error: {res.text}")

    return res.json().get("id")  # message_id
