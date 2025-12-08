# src/payslip/service.py
from datetime import datetime, date

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.payslip.models import PayslipRequest, PayslipStatus
from src.core.models import Users, Roles, UserTeamsRole, Teams
from src.payslip.schemas import PayslipRequestSchema
from src.payslip.utils import calculate_period, validate_join_date
from src.payslip.googleservice import (
    refresh_google_access_token,
    build_email,
    send_gmail,
)

from src.payslip.utils import decrypt_token
from src.payslip.utils import encrypt_token


async def user_team_name(session: AsyncSession, user_id):
    """Return user's team name."""
    q = select(UserTeamsRole).where(UserTeamsRole.user_id == user_id)
    mapping = (await session.execute(q)).scalar_one_or_none()

    if not mapping:
        return "Unknown Team"

    team = await session.get(Teams, mapping.team_id)
    return team.name if team else "Unknown Team"


async def one_request_per_day(session: AsyncSession, user_id):
    """
    Enforce: one payslip REQUEST per calendar day.
    We count only rows where status != PENDING (i.e., actual requests),
    so that the Gmail-connect row (status=PENDING) does NOT block.
    """
    today_start = datetime.combine(date.today(), datetime.min.time())

    q = select(PayslipRequest).where(
        PayslipRequest.user_id == user_id,
        PayslipRequest.requested_at >= today_start,
        PayslipRequest.status != PayslipStatus.PENDING,
    )

    result = await session.execute(q)
    if result.scalar_one_or_none():
        raise HTTPException(400, "You already sent a payslip request today.")


async def get_hr_email(session: AsyncSession):
    q = select(Roles).where(Roles.name == "HR")
    role = (await session.execute(q)).scalar_one_or_none()
    if not role:
        raise HTTPException(500, "HR role missing")

    q2 = select(UserTeamsRole).where(UserTeamsRole.role_id == role.id)
    mapping = (await session.execute(q2)).scalar_one_or_none()

    if not mapping:
        raise HTTPException(500, "No HR manager mapped")

    hr = await session.get(Users, mapping.user_id)
    return hr.email_id


async def get_latest_payslip_row(session: AsyncSession, user_id):
    """
    Get the most recent payslip row for this user (any status).
    We use this to get the refresh_token and to decide whether to update or insert.
    """
    q = (
        select(PayslipRequest)
        .where(PayslipRequest.user_id == user_id)
        .order_by(PayslipRequest.requested_at.desc())
    )
    return (await session.execute(q)).scalar_one_or_none()


async def process_payslip_request(
    session: AsyncSession, user: Users, payload: PayslipRequestSchema
):
    # 1. Only ONE request per day (for actual payslip sends)
    await one_request_per_day(session, user.id)

    # 2. Validate period based on mode + months
    period_start, period_end = calculate_period(
        payload.mode,
        payload.start_month,
        payload.end_month,
    )

    # 3. Validate join date
    validate_join_date(user.join_date, period_start)

    # 4. Get refresh_token from latest payslip row (DB)
    latest = await get_latest_payslip_row(session, user.id)

    refresh_token = decrypt_token(latest.refresh_token) if latest else None

    if not refresh_token:
        # No token stored yet
        raise HTTPException(
            400, "Please connect your Gmail account before requesting payslip."
        )

    # 5. Refresh access token with Google
    access_token = refresh_google_access_token(refresh_token)

    # 6. Get HR email
    hr_email = await get_hr_email(session)

    # 7. Get team name
    team = await user_team_name(session, user.id)

    # 8. Build email body
    subject = "Payslip Request"
    body = (
        f"Dear Team,\n\n"
        f"I would like to request the payslip for the following period:\n\n"
        f"Employee Name : {user.user_name}\n"
        f"Email         : {user.email_id}\n"
        f"Team          : {team}\n"
        f"Period        : {period_start} → {period_end}\n\n"
        f"Kindly process this request at the earliest.\n"
        f"Thank you.\n"
    )

    raw = build_email(user.email_id, hr_email, subject, body)

    # 9. Send email via Gmail API
    send_gmail(access_token, raw)

    # 10. Decide whether to UPDATE existing row or CREATE a new one
    now = datetime.now()

    if latest and latest.status == PayslipStatus.PENDING:
        # This is the "connection row" (created when Gmail was connected)
        # ✅ Update this row with today's request info
        latest.status = PayslipStatus.SENT
        latest.requested_at = now
        latest.error_message = None
        latest.refresh_token = encrypt_token(refresh_token)  # keep token
        session.add(latest)
        await session.commit()
        await session.refresh(latest)
        return latest
    else:
        # Either no row existed, or latest is already SENT/FAILED.
        # ✅ Create a new row for this request, copying the refresh token.
        entry = PayslipRequest(
            user_id=user.id,
            status=PayslipStatus.SENT,
            requested_at=now,
            refresh_token=refresh_token,
            error_message=None,
        )

        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry
