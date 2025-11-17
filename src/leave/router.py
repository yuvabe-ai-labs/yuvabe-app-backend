from src.leave.utils import send_email
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.utils import get_current_user
from src.core.database import get_async_session
from src.core.models import Users, Teams, Roles, UserTeamsRole
from src.auth.schemas import BaseResponse
from fastapi import BackgroundTasks

router = APIRouter(prefix="/leave", tags=["leave"])


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
