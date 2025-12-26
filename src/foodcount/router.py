from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.models import Users
from src.foodcount.schemas import LunchNotifyRequest, LunchNotifyResponse
from src.foodcount.service import process_lunch_notification
from src.auth.utils import get_current_user

router = APIRouter(prefix="/lunch", tags=["Lunch"])


@router.post(
    "/notify",
    response_model=LunchNotifyResponse,
)
async def notify_lunch_manager(
    payload: LunchNotifyRequest,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    sent_to = await process_lunch_notification(
        session=session,
        user_id=user,
        payload=payload,
    )

    return {
        "status": "sent",
        "sent_to": sent_to,
    }
