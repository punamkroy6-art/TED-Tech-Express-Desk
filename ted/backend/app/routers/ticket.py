import uuid as _uuid
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, cast, String
from app.database import get_db
from app.services import auth_service
from app.services.freshworks import create_ticket
from app.models.session import Session as KioskSession
from app.models.diagnosis import DiagnosisResult
from app.models.employee import Employee

router = APIRouter()


class TicketRequest(BaseModel):
    device_serial: str = ""


@router.post("/ticket")
async def create_freshworks_ticket(
    body: TicketRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    session_id = claims["session_id"]

    # Fetch latest diagnosis for this session (cast to string for SQLite compat)
    try:
        sid = _uuid.UUID(session_id)
    except ValueError:
        sid = session_id
    diag_result = await db.execute(
        select(DiagnosisResult)
        .where(cast(DiagnosisResult.session_id, String) == str(sid))
        .order_by(DiagnosisResult.created_at.desc())
        .limit(1)
    )
    diag = diag_result.scalar_one_or_none()

    # Fetch employee
    emp_result = await db.execute(
        select(Employee).where(Employee.employee_id == claims["sub"])
    )
    employee = emp_result.scalar_one_or_none()
    employee_dict = {}
    if employee:
        employee_dict = {
            "id": employee.employee_id,
            "name": employee.display_name,
            "freshworks_id": employee.freshworks_id,
        }

    diagnosis_dict = {}
    if diag:
        diagnosis_dict = {
            "diagnosis": diag.diagnosis or "Issue reported via TED kiosk",
            "confidence": diag.confidence or 0,
            "severity": diag.severity or "medium",
            "fix_steps": diag.fix_steps or [],
            "suggested_group": diag.suggested_group or "IT_SD",
        }
    else:
        diagnosis_dict = {
            "diagnosis": "Issue reported via TED kiosk — no AI diagnosis available",
            "confidence": 0,
            "severity": "medium",
            "fix_steps": [],
            "suggested_group": "IT_SD",
        }

    ticket = await create_ticket(session_id, diagnosis_dict, employee_dict, body.device_serial)
    return ticket
