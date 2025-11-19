from src.profile.service import send_email_service
from src.profile.schemas import SendMailRequest
from src.profile.utils import build_auth_url
from src.profile.utils import exchange_code_for_tokens
from src.profile.service import USER_TOKEN_STORE
from src.profile.utils import send_email
from src.profile.service import list_user_assets
from fastapi.routing import APIRouter
from src.core.database import get_async_session
from src.auth.utils import get_current_user
from src.auth.schemas import BaseResponse
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi.params import Depends
from .schemas import UpdateProfileRequest
from src.profile.service import update_user_profile
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import select
from src.core.models import Users, Teams, Roles, UserTeamsRole
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.utils import get_current_user  # adjust path
from src.profile.schemas import (
    ApplyLeaveRequest,
    ApproveRejectRequest,
    LeaveResponse,
    BalanceResponse,
    DeviceTokenIn,
)
from src.profile import service
from typing import List


router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("/apply", response_model=LeaveResponse)
async def apply_leave_endpoint(
    payload: ApplyLeaveRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    user_id = current_user
    leave = await service.apply_leave(session, user_id, payload)
    return leave


@router.get("/pending", response_model=List[LeaveResponse])
async def pending_leaves(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    user_id = current_user
    leaves = await service.get_pending_leaves_for_approver(session, user_id)
    return leaves


@router.get("/my", response_model=List[LeaveResponse])
async def my_leaves(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    leaves = await service.get_my_leaves(session, current_user)
    return leaves


@router.get("/team", response_model=List[LeaveResponse])
async def team_leaves(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    leaves = await service.get_team_leaves(session, current_user)
    return leaves


@router.post("/{leave_id}/approve", response_model=LeaveResponse)
async def approve_leave_endpoint(
    leave_id: str,
    payload: ApproveRejectRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    leave = await service.approve_leave(
        session, current_user, leave_id, comment=payload.comment
    )
    return leave


@router.post("/{leave_id}/reject", response_model=LeaveResponse)
async def reject_leave_endpoint(
    leave_id: str,
    payload: ApproveRejectRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    leave = await service.reject_leave(
        session,
        current_user,
        leave_id,
        reject_reason=payload.reject_reason,
        comment=payload.comment,
    )
    return leave


@router.get("/balance", response_model=List[BalanceResponse])
async def get_balance(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    return await service.get_leave_balance(session, current_user)


@router.post("/device-token")
async def save_device_token(
    payload: DeviceTokenIn,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    tokens = await service.add_device_token(session, current_user, payload.device_token)
    return {"status": "ok", "tokens": tokens}




@router.get("/login")
def google_login(state: str | None = Query(None)):
    return RedirectResponse(build_auth_url(state))


@router.get("/callback")
async def google_callback(code: str | None = None, state: str | None = None):
    if not code:
        raise HTTPException(400, "Missing code")

    token_data = await exchange_code_for_tokens(code)
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")

    # Get user info
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    userinfo = r.json()

    google_user_id = userinfo["sub"]
    user_email = userinfo["email"]

    USER_TOKEN_STORE[google_user_id] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "email": user_email,
    }

    return JSONResponse(
        {
            "status": "ok",
            "user_id": google_user_id,
            "email": user_email,
            "state": state,
        }
    )


@router.post("/send-mail")
async def send_mail(req: SendMailRequest):
    return await send_email_service(req)


@router.get("/", response_model=BaseResponse)
async def get_assets(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
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


@router.put("/update-profile", response_model=BaseResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await update_user_profile(session, user_id, payload)
    return {"code": 200, "data": result}


@router.get("/contacts", response_model=BaseResponse)
async def get_leave_contacts(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # get_current_user returns a STRING user_id
    user_id = current_user

    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user token")

    # 1) Get user's team
    stmt = select(UserTeamsRole).where(UserTeamsRole.user_id == user_id)
    ut = (await session.exec(stmt)).first()

    if not ut:
        raise HTTPException(status_code=404, detail="User-Team mapping not found")

    # 2) Get Team Lead role
    lead_role = (
        await session.exec(select(Roles).where(Roles.name == "Team Lead"))
    ).first()

    if not lead_role:
        raise HTTPException(status_code=500, detail="Team Lead role not found")

    # 3) Find Team Lead user in same team
    lead_user = (
        await session.exec(
            select(Users)
            .join(UserTeamsRole)
            .where(UserTeamsRole.team_id == ut.team_id)
            .where(UserTeamsRole.role_id == lead_role.id)
        )
    ).all()

    if not lead_user:
        raise HTTPException(status_code=404, detail="Team lead not found")

    to_email = ", ".join([u.email_id for u in lead_user])

    # 4) HR CC emails
    hr_team = (await session.exec(select(Teams).where(Teams.name == "HR Team"))).first()

    cc = []
    if hr_team:
        hr_users = (
            await session.exec(
                select(Users)
                .join(UserTeamsRole)
                .where(UserTeamsRole.team_id == hr_team.id)
            )
        ).all()

        cc = [str(row.email_id) for row in hr_users]

    return BaseResponse(code=200, message="success", data={"to": to_email, "cc": cc})


@router.post("/send", response_model=BaseResponse)
async def send_leave_email(
    payload: dict,
    background: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    from_email = payload.get("from_email")
    to_email = payload.get("to")
    cc = payload.get("cc", [])
    subject = payload.get("subject")
    body = payload.get("body")

    if not subject or not body:
        raise HTTPException(status_code=400, detail="Subject and body required")

    # send in background so API returns fast
    background.add_task(send_email, to_email, subject, body, cc, from_email)

    return BaseResponse(code=200, message="Leave request sent", data=None)
