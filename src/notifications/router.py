from src.profile.models import UserDevices
from src.profile.models import Leave
from sqlmodel import select
from requests.api import delete
from src.notifications.schemas import RegisterDeviceRequest
from src.notifications.service import register_device
from fastapi import APIRouter, Depends
from src.auth.utils import get_current_user
from src.core.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
import uuid

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/register-device")
async def register_device_route(
    body: RegisterDeviceRequest,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    device = await register_device(user, body, session)
    return {"message": "Device registered", "device": str(device.id)}


@router.post("/{notif_id}/mark-read")
async def mark_notification_read(
    notif_id: str,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    notif = await session.get(Leave, uuid.UUID(notif_id))

    if not notif:
        raise HTTPException(404, "Notification not found")

    # Only owner or mentor should mark
    if str(notif.user_id) != user_id and str(notif.mentor_id) != user_id:
        raise HTTPException(403, "Unauthorized")

    notif.is_read = True
    await session.commit()

    return {"message": "Marked as read"}


@router.post("/logout")
async def logout(
    body: RegisterDeviceRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    stmt = select(UserDevices).where(
        UserDevices.user_id == user_id, UserDevices.device_token == body.device_token
    )
    result = await session.execute(stmt)
    device = result.scalar_one_or_none()

    if not device:
        return {"message": "Device already removed"}

    await session.delete(device)
    await session.commit()

    return {"message": "Logged out — device token removed"}


@router.post("/mark-all-read")
async def mark_all_read(
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    await session.execute(
        text(
            """
            UPDATE leave
            SET is_read = TRUE
            WHERE user_id = :uid OR mentor_id = :uid
        """
        ),
        {"uid": user_id},
    )
    await session.commit()

    return {"message": "All notifications cleared"}


