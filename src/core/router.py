from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.core.database import get_async_session
from src.core.schemas import BaseResponse
from src.core.models import AppVersion
from .schemas import AppConfigResponse

router = APIRouter(prefix="/app", tags=["AppConfig"])


@router.get("/config", response_model=BaseResponse[AppConfigResponse])
async def get_app_config(
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.exec(select(AppVersion))
    row = result.first()

    min_version = row.version if row else "0.0.0"
    apk_url = row.apk_download_link if row else ""
    ios_url = row.ios_download_link if row else ""

    return BaseResponse(
        status_code=200,
        data=AppConfigResponse(
            version=min_version,
            apk_download_link=apk_url,
            ios_download_link=ios_url
        )
    )


