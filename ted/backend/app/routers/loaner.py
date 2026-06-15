from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import auth_service

router = APIRouter()


class LoanerRequest(BaseModel):
    device_type: str = "laptop"  # 'laptop' | 'charger' | 'mouse'
    reason: str = ""


@router.post("/loaner/request")
async def create_loaner_request(
    body: LoanerRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Phase 1: mock loaner — locker hardware integration in Phase 2
    loaner_id = f"LOAN-{claims['session_id'][:8].upper()}"
    return {
        "loaner_id": loaner_id,
        "device_type": body.device_type,
        "locker_bay": "A3",
        "status": "dispensing",
        "message": f"Please collect your {body.device_type} from Locker Bay A3.",
    }
