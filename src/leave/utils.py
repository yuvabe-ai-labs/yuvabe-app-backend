# src/core/email_utils.py
import smtplib
from email.message import EmailMessage
from src.core.config import settings
from typing import List


SMTP_HOST = settings.EMAIL_SERVER
SMTP_PORT = settings.EMAIL_PORT
SMTP_USER = settings.EMAIL_USERNAME
SMTP_PASS = settings.EMAIL_PASSWORD
FROM_DEFAULT = settings.EMAIL_USERNAME


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
