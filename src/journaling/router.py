import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.database import get_async_session
from src.core.schemas import BaseResponse
from src.auth.utils import get_current_user

from src.journaling.schemas import (
    JournalCreate,
    JournalUpdate,
    JournalResponse,
)
from src.journaling.service import (
    create_or_update_journal,
    get_all_journals,
    get_journal,
    update_journal,
    delete_journal,
)

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post("/", response_model=BaseResponse[JournalResponse], status_code=200)
async def create_or_update(
    data: JournalCreate,
    user_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    data.user_id = user_id

    try:
        record = await create_or_update_journal(data, session)
        return BaseResponse(status_code=200, data=record)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=BaseResponse[list[JournalResponse]], status_code=200)
async def list_user_journals(
    user_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    records = await get_all_journals(user_id, session)
    return BaseResponse(status_code=200, data=records)


@router.get("/entry/{journal_id}", response_model=BaseResponse[JournalResponse], status_code=200)
async def fetch_single(
    journal_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        record = await get_journal(journal_id, user_id, session)
        return BaseResponse(status_code=200, data=record)
    except ValueError as e:
        if str(e) == "Not authorized":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/entry/{journal_id}", response_model=BaseResponse[JournalResponse], status_code=200)
async def update_entry(
    journal_id: uuid.UUID,
    data: JournalUpdate,
    user_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        record = await update_journal(journal_id, data, user_id, session)
        return BaseResponse(status_code=200, data=record)
    except ValueError as e:
        if str(e) == "Not authorized":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/entry/{journal_id}", response_model=BaseResponse[str], status_code=200)
async def delete_entry(
    journal_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        await delete_journal(journal_id, user_id, session)
        return BaseResponse(status_code=200, data="Deleted")
    except ValueError as e:
        if str(e) == "Not authorized":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))
