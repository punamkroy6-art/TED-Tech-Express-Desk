import base64
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from app.services import auth_service

router = APIRouter()


class OCRRequest(BaseModel):
    image_b64: str  # base64-encoded image
    mime_type: str = "image/png"


@router.post("/ocr")
async def run_ocr(
    body: OCRRequest,
    authorization: str = Header(...),
):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Phase 1: mock OCR response — PaddleOCR integration in Phase 2
    return {
        "text": "Sample OCR output — PaddleOCR integration coming in Phase 2.",
        "confidence": 0.0,
        "blocks": [],
    }
