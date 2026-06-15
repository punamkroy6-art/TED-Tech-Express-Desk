import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db, get_redis
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_ok = False
    redis_ok = False
    details = {}
    
    # 1. Test database connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
        details["database"] = "online"
    except Exception as e:
        details["database"] = f"offline (Error: {str(e)})"
        
    # 2. Test Redis connectivity
    try:
        redis_client = await get_redis()
        # Redis ping
        await redis_client.ping()
        redis_ok = True
        details["redis"] = "online"
        await redis_client.close()
    except Exception as e:
        details["redis"] = f"offline (Error: {str(e)})"
        
    # If any core component is down, return a 503 status code
    if not (db_ok and redis_ok):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "degraded",
                **details
            }
        )
        
    return {
        "status": "healthy",
        **details
    }


@router.get("/health/freshworks")
async def freshworks_health():
    """Test the Freshservice API connection — call this after updating .env"""
    if not settings.freshworks_domain or not settings.freshworks_api_key:
        return {
            "status": "not_configured",
            "message": "Set FRESHWORKS_DOMAIN and FRESHWORKS_API_KEY in .env then restart the backend.",
            "docs": "https://support.freshservice.com/en/support/solutions/articles/50000000138"
        }

    from app.services.freshworks import _get_base_url, _get_headers
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{_get_base_url()}/tickets?per_page=1",
                headers=_get_headers()
            )
        if r.status_code == 200:
            return {"status": "connected", "domain": settings.freshworks_domain,
                    "message": "Freshservice API is reachable and credentials are valid ✓"}
        elif r.status_code == 401:
            return {"status": "auth_failed",
                    "message": "API key is wrong or not Base64 encoded correctly.",
                    "hint": "Run: python -c \"import base64; print(base64.b64encode(b'YOUR_KEY:X').decode())\""}
        elif r.status_code == 403:
            return {"status": "forbidden",
                    "message": "API key is valid but lacks ticket permissions — check agent role in Freshservice."}
        else:
            return {"status": "error", "http_status": r.status_code, "body": r.text[:200]}
    except httpx.ConnectError:
        return {"status": "unreachable",
                "message": f"Cannot reach {settings.freshworks_domain} — check the domain name."}
