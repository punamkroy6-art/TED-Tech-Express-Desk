"""
/api/diagnostic/* — Auto Diagnostic & Camera Endpoints

Software diagnostics: OS, drivers, processes, network
Hardware diagnostics: CPU, RAM, disk, battery, USB, thermal
Camera 0: Screen capture (employee's laptop screen → OCR)
Camera 1: Hardware inspection (device scan → barcode/QR)
Camera 2: Badge/employee camera (auto-authentication)
"""
import asyncio
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import auth_service

router = APIRouter()


def _require_auth(authorization: str) -> dict:
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── Full Auto-Diagnostic (Software + Hardware combined) ───────────────────

@router.post("/diagnostic/run")
async def run_full_diagnostic(authorization: str = Header(...)):
    """
    Run complete auto-diagnostic: software + hardware.
    Called automatically when employee selects 'Fix an IT Issue'.
    Returns consolidated health report with issue summary.
    """
    _require_auth(authorization)

    loop = asyncio.get_event_loop()

    # Run both diagnostics concurrently
    sw_task = loop.run_in_executor(None, _run_software)
    hw_task = loop.run_in_executor(None, _run_hardware)
    sw_result, hw_result = await asyncio.gather(sw_task, hw_task)

    # Combine issues
    all_issues = sw_result.get("issues_found", []) + hw_result.get("issues_found", [])
    overall_health = "critical" if any(r.get("health") == "critical" for r in [sw_result, hw_result]) else \
                     "warning" if all_issues else "healthy"

    return {
        "overall_health": overall_health,
        "issues_found": all_issues,
        "software": sw_result,
        "hardware": hw_result,
        "auto_fix_recommended": bool(all_issues),
        "suggested_queries": _build_suggested_queries(all_issues, sw_result, hw_result),
    }


def _run_software():
    from app.services.diagnostics.software import run_full_software_diagnostic
    return run_full_software_diagnostic()


def _run_hardware():
    from app.services.diagnostics.hardware import run_full_hardware_diagnostic
    return run_full_hardware_diagnostic()


def _build_suggested_queries(issues: list, sw: dict, hw: dict) -> list[str]:
    """Convert diagnostic findings into natural-language queries for the AI engine."""
    queries = []
    mem_pct = hw.get("memory", {}).get("percent", 0)
    cpu_pct = hw.get("cpu", {}).get("percent", 0)
    disk_free = hw.get("disk", {}).get("primary", {}).get("free_gb", 99)
    battery_pct = hw.get("battery", {}).get("percent", 100)

    if mem_pct > 88:
        queries.append(f"computer running slow memory usage at {mem_pct}%")
    if cpu_pct > 85:
        queries.append(f"CPU at {cpu_pct}% high usage freezing")
    if disk_free < 5:
        queries.append(f"disk full only {disk_free} GB free no space left")
    if battery_pct < 15 and hw.get("battery", {}).get("present"):
        queries.append(f"battery critically low at {battery_pct}%")

    failed_drivers = sw.get("drivers", {}).get("failed_drivers", [])
    if failed_drivers:
        queries.append(f"driver error {failed_drivers[0].get('name','device')} not working")

    net = sw.get("network", {})
    if net.get("internet") == "failed":
        queries.append("cannot connect to internet network down")

    return queries or ["computer running slowly general issue"]


# ── Software Diagnostics only ─────────────────────────────────────────────

@router.get("/diagnostic/software")
async def run_software_diagnostic(authorization: str = Header(...)):
    """Run software-only diagnostic: OS, drivers, processes, network."""
    _require_auth(authorization)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_software)
    return result


# ── Hardware Diagnostics only ─────────────────────────────────────────────

@router.get("/diagnostic/hardware")
async def run_hardware_diagnostic(authorization: str = Header(...)):
    """Run hardware-only diagnostic: CPU, RAM, disk, battery, USB, thermal."""
    _require_auth(authorization)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_hardware)
    return result


# ── Camera: List all cameras ──────────────────────────────────────────────

@router.get("/camera/list")
async def list_cameras(authorization: str = Header(...)):
    """List all connected cameras with their roles and live preview."""
    _require_auth(authorization)
    loop = asyncio.get_event_loop()
    try:
        from app.services.diagnostics.cameras import list_available_cameras
        cameras = await loop.run_in_executor(None, list_available_cameras)
        return {
            "cameras": cameras,
            "total": len(cameras),
            "roles": {
                "camera_0": "Screen Capture — points at employee laptop screen",
                "camera_1": "Hardware Inspection — points at physical device",
                "camera_2": "Badge / Employee — faces the employee",
            }
        }
    except Exception as e:
        return {"cameras": [], "total": 0, "error": str(e)}


# ── Camera 0: Screen Capture → OCR-ready ─────────────────────────────────

@router.post("/camera/screen/capture")
async def capture_screen(authorization: str = Header(...)):
    """
    Camera 0 — Capture employee's laptop screen.
    Returns JPEG image + BSOD/error dialog detection flags.
    Pass image_b64 to /api/ocr to extract error text.
    """
    _require_auth(authorization)
    loop = asyncio.get_event_loop()
    try:
        from app.services.diagnostics.cameras import capture_screen as _cap
        result = await loop.run_in_executor(None, _cap)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Camera 1: Hardware Scan → QR/Barcode ─────────────────────────────────

@router.post("/camera/hardware/scan")
async def scan_hardware(authorization: str = Header(...)):
    """
    Camera 1 — Scan the physical device.
    Reads asset tag, serial number via QR/barcode.
    Checks physical condition (damage detection).
    """
    _require_auth(authorization)
    loop = asyncio.get_event_loop()
    try:
        from app.services.diagnostics.cameras import scan_hardware_device
        result = await loop.run_in_executor(None, scan_hardware_device)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Camera 2: Badge Scan → Auto-Login ────────────────────────────────────

@router.post("/camera/badge/scan")
async def scan_badge():
    """
    Camera 2 — Scan employee badge QR code.
    No auth required — this IS the authentication step.
    Returns employee_id to pass to /api/auth/session.
    """
    loop = asyncio.get_event_loop()
    try:
        from app.services.diagnostics.cameras import scan_badge as _scan
        result = await loop.run_in_executor(None, _scan)
        return result
    except Exception as e:
        return {"success": False, "error": str(e),
                "tip": "Ensure Camera 2 is connected and pointed at the employee badge"}


# ── Camera: Status check for all 3 cameras ───────────────────────────────

@router.get("/camera/status")
async def camera_status():
    """Check which cameras are connected — no auth required (shown on idle screen)."""
    loop = asyncio.get_event_loop()
    try:
        from app.services.diagnostics.cameras import capture_all_cameras
        result = await loop.run_in_executor(None, capture_all_cameras)
        return {
            "status": "ok",
            "cameras": result,
            "connected_count": sum(1 for c in result.values() if c.get("connected")),
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "cameras": {}}
