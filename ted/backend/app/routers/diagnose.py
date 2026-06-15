import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import auth_service, ai_engine

router = APIRouter()


class DiagnoseRequest(BaseModel):
    error_text: str
    device_info: dict = {}
    issue_type: str = "software"  # 'software'|'hardware'|'network'


@router.post("/diagnose")
async def run_diagnose(
    body: DiagnoseRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    session_id = claims.get("session_id", str(uuid.uuid4()))
    result = await ai_engine.run_diagnosis(session_id, body.model_dump())
    return result


@router.get("/diagnose/{job_id}")
async def get_diagnose_status(job_id: str):
    # Phase 1: diagnosis is synchronous so this just confirms completion
    return {"job_id": job_id, "status": "completed"}
