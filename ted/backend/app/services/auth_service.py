import uuid
from datetime import datetime, timedelta
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.config import settings
from app.models.employee import Employee
from app.models.session import Session as KioskSession


def create_token(employee_id: str, session_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiry_minutes)
    payload = {
        "sub": employee_id,
        "session_id": session_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")


async def get_or_create_employee(db: AsyncSession, employee_id: str, display_name: str = None, email: str = None) -> Employee:
    result = await db.execute(select(Employee).where(Employee.employee_id == employee_id))
    employee = result.scalar_one_or_none()
    if employee is None:
        employee = Employee(
            employee_id=employee_id,
            display_name=display_name or employee_id,
            email=email or f"{employee_id}@company.com",
        )
        db.add(employee)
        await db.commit()
        await db.refresh(employee)
    else:
        employee.last_seen = datetime.utcnow()
        await db.commit()
    return employee


async def create_kiosk_session(db: AsyncSession, employee_id: str, kiosk_id: str, auth_method: str) -> KioskSession:
    session = KioskSession(
        employee_id=employee_id,
        kiosk_id=kiosk_id,
        auth_method=auth_method,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def end_kiosk_session(db: AsyncSession, session_id: str, outcome: str, csat_score: int | None = None):
    from sqlalchemy import cast, String
    now = datetime.utcnow()
    result = await db.execute(
        select(KioskSession).where(cast(KioskSession.id, String) == str(session_id))
    )
    session = result.scalar_one_or_none()
    if session:
        session.ended_at = now
        if session.started_at:
            session.duration_secs = int((now - session.started_at).total_seconds())
        session.outcome = outcome
        if csat_score is not None and 1 <= csat_score <= 5:
            session.csat_score = csat_score
        await db.commit()
