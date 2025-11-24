from src.profile.models import UserDevices
from src.notifications.schemas import RegisterDeviceRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime


async def register_device(
    user_id: str, body: RegisterDeviceRequest, session: AsyncSession
):

    # Check if the user already has this token saved
    stmt = select(UserDevices).where(
        UserDevices.user_id == user_id,
        UserDevices.device_token == body.device_token,
    )
    result = await session.execute(stmt)
    device = result.scalar_one_or_none()

    if device:
        device.platform = body.platform
        device.device_model = body.device_model
        device.last_seen = datetime.utcnow()
        device.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(device)
        return device

    # Create new device entry
    new_device = UserDevices(
        user_id=user_id,
        device_token=body.device_token,
        platform=body.platform,
        device_model=body.device_model,
    )

    session.add(new_device)
    await session.commit()
    await session.refresh(new_device)
    return new_device

from sqlalchemy import select
from src.profile.models import UserDevices

async def get_user_device_tokens(session, user_id):
    stmt = select(UserDevices.device_token).where(UserDevices.user_id == user_id)
    rows = (await session.execute(stmt)).all()
    return [r[0] for r in rows]
