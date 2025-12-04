from sqlmodel import Session, select
from fastapi import HTTPException
from src.payslip.models import PayslipRequest, PayslipStatus
from src.core.models import Users, Roles, UserTeamsRole

from src.payslip.utils import calculate_period, validate_join_date
from src.payslip.googleservice import (
    refresh_google_access_token,
    build_email,
    send_gmail,
)


def get_latest_refresh_token(session: Session, user_id):
    stmt = (
        select(PayslipRequest)
        .where(
            PayslipRequest.user_id == user_id,
            PayslipRequest.refresh_token.is_not(None),
        )
        .order_by(PayslipRequest.requested_at.desc())
    )
    entry = session.exec(stmt).first()
    return entry.refresh_token if entry else None


def get_hr_email(session: Session) -> str:
    role = session.exec(select(Roles).where(Roles.name == "HR Manager")).first()
    if not role:
        raise HTTPException(500, "HR Manager role missing")

    mapping = session.exec(
        select(UserTeamsRole).where(UserTeamsRole.role_id == role.id)
    ).first()

    if not mapping:
        raise HTTPException(500, "No HR assigned")

    hr_user = session.get(Users, mapping.user_id)
    return hr_user.email_id


def process_payslip_request(session: Session, user: Users, payload):
    # 1. Compute period
    period_start, period_end = calculate_period(
        payload.mode, payload.start_month, payload.end_month
    )

    # 2. Validate join date
    validate_join_date(user.join_date, period_start)

    # 3. Find refresh_token
    refresh_token = get_latest_refresh_token(session, user.id)

    if not refresh_token:
        raise HTTPException(
            400, "Please connect your Gmail before requesting a payslip."
        )

    # 4. Get access token
    access_token = refresh_google_access_token(refresh_token)

    # 5. Find HR email
    hr_email = get_hr_email(session)

    # 6. Build message
    subject = "Payslip Request"
    body = (
        f"Payslip request from {user.email_id}\n"
        f"Period: {period_start} → {period_end}"
    )
    raw = build_email(user.email_id, hr_email, subject, body)

    # 7. Send email
    message_id = send_gmail(access_token, raw)

    # 8. Create new DB record
    entry = PayslipRequest(
        user_id=user.id,
        status=PayslipStatus.SENT,
        refresh_token=refresh_token,
        error_message=None,
    )

    session.add(entry)
    session.commit()
    session.refresh(entry)

    return entry
