from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from src.core.models import Users, Roles, UserTeamsRole
from src.foodcount.schemas import LunchNotifyRequest
from src.core.utils import send_mail_as_user
from src.core.models import LunchLocation

LOCATION_ROLE_MAP = {
    LunchLocation.SOLAR_KITCHEN: "LM - Solar Kitchen",
    LunchLocation.SARACON_CAMPUS: "LM - Saracon Campus",
}

async def get_lunch_manager_by_location(
    session: AsyncSession,
    location: LunchLocation,
) -> Users:

    role_name = LOCATION_ROLE_MAP.get(location)
    if not role_name:
        raise HTTPException(400, "Invalid lunch location")

    role = (
        await session.execute(
            select(Roles).where(Roles.name == role_name)
        )
    ).scalar_one_or_none()

    if not role:
        raise HTTPException(500, "Lunch manager role missing")

    mapping = (
        await session.execute(
            select(UserTeamsRole)
            .where(UserTeamsRole.role_id == role.id)
        )
    ).scalars().first()

    if not mapping:
        raise HTTPException(500, "No lunch manager assigned")

    manager = await session.get(Users, mapping.user_id)
    if not manager:
        raise HTTPException(500, "Manager user not found")

    return manager

def build_lunch_mail_body(
    user_name: str,
    email: str,
    location: LunchLocation,
    start_date,
    end_date,
):
    if start_date == end_date:
        date_text = start_date.strftime("%d %b %Y")
    else:
        date_text = f"{start_date} to {end_date}"

    return (
        f"Employee Name : {user_name}\n"
        f"Email         : {email}\n"
        f"Location      : {location}\n"
        f"Dates         : {date_text}\n\n"
        f"The user has opted out of lunch."
    )

async def process_lunch_notification(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: LunchNotifyRequest,
):
    # fetch only needed user fields
    row = (
        await session.execute(
            select(
                Users.user_name,
                Users.email_id,
                Users.lunch_preference,
            ).where(Users.id == user_id)
        )
    ).one_or_none()

    if not row:
        raise HTTPException(404, "User not found")

    user_name, email_id, lunch_pref = row

    if not lunch_pref:
        raise HTTPException(400, "Lunch preference not set")

    manager = await get_lunch_manager_by_location(session, lunch_pref)

    body = build_lunch_mail_body(
        user_name=user_name,
        email=email_id,
        location=lunch_pref,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    try:
        await send_mail_as_user(
            session=session,
            user_id=user_id,
            from_email=email_id,
            to_email=manager.email_id,
            subject="Lunch Opt-out Notification",
            body=body,
        )
    except HTTPException as e:
            if e.status_code == 428:
                raise HTTPException(
                    status_code=428,
                    detail="Please connect your Gmail account"
                )
            raise

    return manager.email_id
