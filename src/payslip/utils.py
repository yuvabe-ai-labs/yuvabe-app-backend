# src/payslip/utils.py
from datetime import date, datetime
from typing import Optional

from dateutil.relativedelta import relativedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_async_session
from src.core.models import Users
from src.core.config import settings

bearer_scheme = HTTPBearer()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM


def _parse_month(month_str: str) -> date:
    """
    "2024-05" -> date(2024, 5, 1)
    """
    try:
        d = datetime.strptime(month_str, "%Y-%m")
        return date(d.year, d.month, 1)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid month format. Use YYYY-MM, e.g. 2024-05",
        )


def validate_join_date(join_date: Optional[str], period_start: date):
    if not join_date:
        return

    join = datetime.strptime(join_date, "%Y-%m-%d").date()
    if period_start < join:
        raise HTTPException(
            400,
            f"You joined on {join}. You cannot request payslips before joining date.",
        )


def calculate_period(mode: str, start_month: str = None, end_month: str = None):
    """
    mode:
      - "3_months"
      - "6_months"
      - "manual" + start_month, end_month in "YYYY-MM"
    """
    today = date.today()

    if mode == "3_months":
        end = today.replace(day=1)
        start = end - relativedelta(months=3)
        return start, end

    if mode == "6_months":
        end = today.replace(day=1)
        start = end - relativedelta(months=6)
        return start, end

    if mode == "manual":
        # Validate fields
        if not start_month or not end_month:
            raise HTTPException(400, "Manual mode requires start_month and end_month")

        try:
            start = datetime.strptime(start_month, "%Y-%m").date()
            end = datetime.strptime(end_month, "%Y-%m").date()
        except ValueError:
            raise HTTPException(400, "Invalid month format. Use YYYY-MM")

        if start > end:
            raise HTTPException(400, "Start month cannot be after end month")

        return start, end

    # Invalid mode
    raise HTTPException(400, "Invalid payslip request mode")


async def get_current_user_model(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(401, "Invalid token")

        result = await session.execute(select(Users).where(Users.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(401, "User not found")

        return user

    except JWTError:
        raise HTTPException(401, "Invalid or expired token")
