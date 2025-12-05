# src/payslip/router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from urllib.parse import urlencode
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.config import settings
from src.core.database import get_async_session
from src.core.models import Users
from src.payslip.schemas import PayslipRequestSchema
from src.payslip.service import process_payslip_request
from src.payslip.googleservice import (
    exchange_code_for_tokens,
    extract_email_from_id_token,
)
from src.payslip.utils import get_current_user_model
from src.payslip.models import PayslipRequest, PayslipStatus

router = APIRouter(prefix="/payslips", tags=["Payslips & Gmail"])


@router.get("/gmail/connect-url")
async def gmail_connect_url(user_id: uuid.UUID):
    """
    Returns the Google OAuth URL for the frontend to open in InAppBrowser.
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.send",
        "access_type": "offline",
        "prompt": "consent",
        "state": str(user_id),
    }
    return {"auth_url": f"{settings.AUTH_BASE}?{urlencode(params)}"}


@router.get("/gmail/callback", response_class=HTMLResponse)
async def gmail_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Google redirects here with ?code & ?state=user_id.
    We:
      - exchange code for tokens
      - verify the Google email matches our user's email
      - store refresh_token into payslip_requests table
    """
    user_id = uuid.UUID(state)
    user = await session.get(Users, user_id)

    if not user:
        raise HTTPException(400, "User not found for given state")

    token_data = exchange_code_for_tokens(code)
    google_email = extract_email_from_id_token(token_data["id_token"])

    if google_email.lower() != user.email_id.lower():
        raise HTTPException(
            400,
            f"Please select your registered email: {user.email_id}",
        )

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(400, "No refresh token received from Google")

    # Check if this user already has any payslip row
    q = (
        select(PayslipRequest)
        .where(PayslipRequest.user_id == user_id)
        .order_by(PayslipRequest.requested_at.desc())
    )
    existing = (await session.execute(q)).scalar_one_or_none()

    if existing:
        # Update the latest row with new refresh token
        existing.refresh_token = refresh_token
        # Do NOT change requested_at or status here;
        # this endpoint is only for (re)connecting Gmail.
        session.add(existing)
    else:
        # First time ever connecting Gmail -> create a "connection row"
        connection_row = PayslipRequest(
            user_id=user_id,
            refresh_token=refresh_token,
            status=PayslipStatus.PENDING,  # not an actual request yet
            # requested_at default is now; one_request_per_day ignores PENDING rows
        )
        session.add(connection_row)

    await session.commit()

    return """
    <html><body>
        <h1>Gmail Connected Successfully ✔</h1>
        <p>You may now request your payslip.</p>
    </body></html>
    """


@router.post("/request")
async def request_payslip(
    payload: PayslipRequestSchema,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user_model),
):
    """
    User hits this when pressing "Request Payslip" in the app.
    We:
      - enforce 1 request per day
      - compute period
      - validate join date
      - load refresh_token from payslip_requests table
      - send email
      - update or create row in payslip_requests
    """
    entry = await process_payslip_request(session, user, payload)
    return {
        "status": entry.status,
        "requested_at": entry.requested_at,
    }
