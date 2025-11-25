from requests.api import delete
from src.notifications.schemas import RegisterDeviceRequest
from src.notifications.service import register_device
from fastapi import APIRouter, Depends
from src.auth.utils import get_current_user
from src.core.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/register-device")
async def register_device_route(
    body: RegisterDeviceRequest,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    device = await register_device(user, body, session)
    return {"message": "Device registered", "device": str(device.id)}


