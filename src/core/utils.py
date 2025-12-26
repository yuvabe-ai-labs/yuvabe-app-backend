from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from src.payslip.models import PayslipRequest
from src.payslip.utils import decrypt_token
from src.payslip.googleservice import (
    refresh_google_access_token,
    build_email,
    send_gmail,
)


async def send_mail_as_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
):
    q = (
        select(PayslipRequest)
        .where(PayslipRequest.user_id == user_id)
        .order_by(PayslipRequest.requested_at.desc())
    )
    entry = (await session.execute(q)).scalar_one_or_none()

    if not entry or not entry.refresh_token:
        raise HTTPException(428, "GMAIL_NOT_CONNECTED")

    refresh_token = decrypt_token(entry.refresh_token)
    access_token = refresh_google_access_token(refresh_token)

    raw = build_email(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
    )

    send_gmail(access_token, raw)

