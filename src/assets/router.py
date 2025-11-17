from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database import get_async_session
from src.auth.utils import get_current_user
from src.assets.schemas import BaseResponse
from src.assets.service import list_user_assets

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("/", response_model=BaseResponse)
async def get_assets(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    assets = await list_user_assets(session, user_id)

    data = {
        "assets": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "status": a.status,
            }
            for a in assets
        ]
    }

    return {"code": 200, "data": data}
    