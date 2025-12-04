from fastapi import APIRouter, Depends
from src.payslip.schemas import PayslipRequestSchema
from src.payslip.service import process_payslip_request
from src.auth.utils import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_async_session
from src.core.models import Users

router = APIRouter(prefix="/payslips", tags=["Payslips"])


@router.post("/request")
def request_payslip(
    payload: PayslipRequestSchema,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    entry = process_payslip_request(session, user, payload)
    return {
        "status": entry.status,
        "requested_at": entry.requested_at,
    }
