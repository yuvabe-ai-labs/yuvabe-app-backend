from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from urllib.parse import urlencode
import uuid

from src.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_async_session
from src.core.models import Users
from src.payslip.models import PayslipRequest
from src.payslip.googleservice import exchange_code_for_tokens


router = APIRouter(prefix="/google", tags=["Google OAuth"])


@router.get("/connect-url")
def get_connect_url(user_id: uuid.UUID):
    """
    App calls this → backend returns Google OAuth URL
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.GMAIL_SEND_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": str(user_id),
    }

    url = f"{settings.AUTH_BASE}?{urlencode(params)}"
    return {"auth_url": url}


@router.get("/callback", response_class=HTMLResponse)
def google_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Google redirects here after user logs in.
    We store the refresh token in payslip table.
    """
    user_id = uuid.UUID(state)
    user = session.get(Users, user_id)

    if not user:
        raise HTTPException(404, "User not found")

    token_data = exchange_code_for_tokens(code)

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(400, "No refresh token received. Try again.")

    # Save refresh token using a dummy payslip entry
    entry = PayslipRequest(
        user_id=user_id,
        refresh_token=refresh_token,
        status="Pending",
    )
    session.add(entry)
    session.commit()

    return """
    <h2>Gmail Connected Successfully!</h2>
    <p>You can close this window.</p>
    """
