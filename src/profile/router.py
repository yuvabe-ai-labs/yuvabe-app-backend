from fastapi.routing import APIRouter
from src.core.database import get_async_session
from src.auth.utils import get_current_user
from src.auth.schemas import BaseResponse
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi.params import Depends
from .schemas import UpdateProfileRequest
from src.profile.service import update_user_profile

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.put("/update-profile", response_model=BaseResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await update_user_profile(session, user_id, payload)
    return {"code": 200, "data": result}
