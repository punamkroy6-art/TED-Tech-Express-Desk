import uuid
import sys
import os
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Header, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import auth_service, ai_engine

# Make the autofix module importable from the backend
_autofix_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # → ted/
if _autofix_path not in sys.path:
    sys.path.insert(0, _autofix_path)

router = APIRouter()


class DiagnoseRequest(BaseModel):
    error_text: str
    device_info: dict = {}
    issue_type: str = "software"  # 'software'|'hardware'|'network'
    employee: dict = {}           # name, id, dept — passed from frontend


def _run_autofix_background(session_id: str, diagnosis: dict, employee: dict):
    """Run hardware diagnostics + autofix engine in the background."""
    try:
        from autofix.engine import AutoFixEngine
        engine = AutoFixEngine()
        result = engine.run(
            session_id=session_id,
            employee=employee,
            diagnosis=diagnosis,
            generate_report=True,
        )
        print(f"[AutoFix] session={session_id[:8]} action={result.action} "
              f"rules={[r['id'] for r in result.triggered_rules]} "
              f"report={os.path.basename(result.report_path or '')}")
    except Exception as e:
        print(f"[AutoFix] ERROR for session={session_id[:8]}: {type(e).__name__}: {e}")


def _get_hardware_metrics() -> dict:
    """Collect live hardware metrics — returns empty dict if psutil unavailable."""
    try:
        from autofix import diagnostics
        m = diagnostics.collect()
        return diagnostics.metrics_to_dict(m)
    except Exception:
        return {}


def _get_hardware_flags(metrics: dict) -> list[str]:
    """Run rule matching against collected metrics — returns list of rule IDs fired."""
    if not metrics:
        return []
    try:
        from autofix.engine import AutoFixEngine
        engine = AutoFixEngine()
        triggered = engine._match_rules(metrics)
        return [r["id"] for r in triggered]
    except Exception:
        return []


@router.post("/diagnose")
async def run_diagnose(
    body: DiagnoseRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    session_id = claims.get("session_id", str(uuid.uuid4()))

    # ── Step 1: Collect live hardware metrics ────────────────────────────
    metrics = await asyncio.get_event_loop().run_in_executor(None, _get_hardware_metrics)
    hardware_flags = _get_hardware_flags(metrics)

    # ── Step 2: Run AI diagnosis (rule engine + LLM) ─────────────────────
    ai_result = await ai_engine.run_diagnosis(session_id, body.model_dump())

    # ── Step 3: Upgrade action if hardware issues found ───────────────────
    # If hardware auto-fixable issues detected → upgrade to self_resolve
    hardware_self_fix = ["HIGH_CPU", "HIGH_MEMORY", "LOW_DISK", "DISK_PERCENT_HIGH"]
    hardware_urgent   = ["LOW_BATTERY"]

    if hardware_flags:
        if any(f in hardware_self_fix for f in hardware_flags):
            # Hardware issue auto-fixable → self_resolve even if AI said guided_fix
            if ai_result.get("action") != "create_ticket":
                ai_result["action"] = "self_resolve"
            # Prepend hardware warning to fix steps
            hw_steps = []
            if "HIGH_CPU" in hardware_flags:
                hw_steps.append(f"⚠ Hardware: CPU usage is high — open Task Manager and close heavy processes.")
            if "HIGH_MEMORY" in hardware_flags:
                pct = metrics.get("memory", {}).get("percent", "?")
                hw_steps.append(f"⚠ Hardware: RAM at {pct}% — restart your device to free memory.")
            if "LOW_DISK" in hardware_flags or "DISK_PERCENT_HIGH" in hardware_flags:
                free = metrics.get("disk", {}).get("free_gb", "?")
                hw_steps.append(f"⚠ Hardware: Disk only {free} GB free — run Disk Cleanup.")
            ai_result["fix_steps"] = hw_steps + (ai_result.get("fix_steps") or [])
        if "LOW_BATTERY" in hardware_flags:
            pct = metrics.get("battery", {}).get("percent", "?")
            ai_result["fix_steps"] = [f"⚠ Battery critically low ({pct}%) — connect to power now."] + (ai_result.get("fix_steps") or [])

    # ── Step 4: Attach hardware data to response ──────────────────────────
    ai_result["hardware_flags"] = hardware_flags
    ai_result["hardware_metrics"] = {
        "cpu_percent":    metrics.get("cpu", {}).get("percent"),
        "memory_percent": metrics.get("memory", {}).get("percent"),
        "disk_free_gb":   metrics.get("disk", {}).get("free_gb"),
        "battery_percent": metrics.get("battery", {}).get("percent"),
    } if metrics else {}

    # ── Step 5: Run full autofix pipeline in background ───────────────────
    # (hardware fix commands + Word report generation)
    employee = body.employee or {"name": claims.get("sub", ""), "id": claims.get("sub", "")}
    background_tasks.add_task(_run_autofix_background, session_id, ai_result, employee)

    return ai_result


@router.get("/diagnose/{job_id}")
async def get_diagnose_status(job_id: str):
    return {"job_id": job_id, "status": "completed"}
