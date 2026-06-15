from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import auth_service

router = APIRouter()


class SessionRequest(BaseModel):
    employee_id: str
    display_name: str = ""
    email: str = ""
    kiosk_id: str = "KIOSK-001"
    auth_method: str = "sso"  # 'sso' | 'badge'


class SessionResponse(BaseModel):
    token: str
    session_id: str
    employee: dict


@router.post("/session", response_model=SessionResponse)
async def create_session(body: SessionRequest, db: AsyncSession = Depends(get_db)):
    employee = await auth_service.get_or_create_employee(
        db, body.employee_id, body.display_name, body.email
    )
    session = await auth_service.create_kiosk_session(
        db, body.employee_id, body.kiosk_id, body.auth_method
    )
    token = auth_service.create_token(body.employee_id, str(session.id))
    return SessionResponse(
        token=token,
        session_id=str(session.id),
        employee={
            "id": employee.employee_id,
            "name": employee.display_name,
            "email": employee.email,
            "dept": employee.department or "",
        },
    )


class OutcomeRequest(BaseModel):
    outcome: str          # 'resolved' | 'ticket_created' | 'abandoned'
    csat_score: int | None = None  # 1–5


@router.post("/session/outcome")
async def set_outcome(
    body: OutcomeRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    await auth_service.end_kiosk_session(db, claims["session_id"], body.outcome, body.csat_score)
    return {"status": "ok"}


@router.delete("/session")
async def delete_session(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    await auth_service.end_kiosk_session(db, claims["session_id"], "abandoned")
    return {"status": "ok"}
