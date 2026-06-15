"""
/api/ticket — Enhanced Freshservice ticket creation
Includes: AI diagnosis history, hardware metrics, auto-fix results,
          screenshot, and Word incident report attachment.
"""
import uuid as _uuid
import os, sys, base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional
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
    # Rich diagnostic context
    screenshot_b64: str = ""         # base64 JPEG of the error screen
    screen_text: str = ""            # visible text extracted from error screen
    diagnostic_data: dict = {}       # hardware + software metrics from /api/diagnostic/run
    autofix_results: list = []       # results from /api/autofix/run (steps + outcomes)
    ai_diagnosis: dict = {}          # full AI engine response
    error_description: str = ""      # employee's own description
    steps_attempted: list = []       # which fix steps the employee ticked


def _build_rich_description(
    diagnosis: dict,
    employee: dict,
    session_id: str,
    body: TicketRequest,
    device_serial: str,
) -> str:
    """Build a comprehensive HTML-formatted ticket description."""

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    conf_pct  = f"{round(diagnosis.get('confidence', 0) * 100)}%"
    severity  = diagnosis.get('severity', 'medium').upper()

    # Fix steps section
    fix_steps = diagnosis.get('fix_steps', [])
    steps_html = ""
    for i, step in enumerate(fix_steps):
        text = step if isinstance(step, str) else (step.get('instruction') or str(step))
        attempted = i < len(body.steps_attempted) and body.steps_attempted[i]
        icon = "✅" if attempted else "⬜"
        steps_html += f"\n    {icon} {i+1}. {text}"

    # Hardware metrics section
    hw = body.diagnostic_data.get('hardware', {})
    sw = body.diagnostic_data.get('software', {})
    hw_section = ""
    if hw:
        hw_section = f"""
--- HARDWARE DIAGNOSTICS ---
CPU:      {hw.get('cpu', {}).get('percent', 'N/A')}% ({hw.get('cpu', {}).get('cores_logical', '?')} cores)
RAM:      {hw.get('memory', {}).get('percent', 'N/A')}% used ({hw.get('memory', {}).get('used_gb', '?')}/{hw.get('memory', {}).get('total_gb', '?')} GB)
Disk:     {hw.get('disk', {}).get('primary', {}).get('percent', 'N/A')}% ({hw.get('disk', {}).get('primary', {}).get('free_gb', '?')} GB free)
Battery:  {f"{hw.get('battery', {}).get('percent', 'N/A')}% {'(plugged)' if hw.get('battery', {}).get('plugged') else '(unplugged)'}" if hw.get('battery', {}).get('present') else 'Desktop'}
"""

    sw_section = ""
    if sw:
        net = sw.get('network', {})
        os_info = sw.get('os', {})
        failed_drivers = sw.get('drivers', {}).get('failed_drivers', [])
        sw_section = f"""
--- SOFTWARE DIAGNOSTICS ---
OS:       {os_info.get('os', 'N/A')} {os_info.get('release', '')} ({os_info.get('hostname', '')})
Internet: {net.get('internet', 'N/A')}
DNS:      {net.get('dns', 'N/A')}
Defender: {'Enabled' if os_info.get('defender_enabled') else 'Disabled/Unknown'}
Failed drivers: {len(failed_drivers)} {('— ' + failed_drivers[0].get('name', '') if failed_drivers else '')}
"""

    # Auto-fix results
    autofix_section = ""
    if body.autofix_results:
        autofix_section = "\n--- AUTO-FIX EXECUTION RESULTS ---"
        for step in body.autofix_results:
            icon = "✅" if step.get('success') else "❌"
            autofix_section += f"\n{icon} {step.get('label', '?')}"
            if step.get('output'):
                autofix_section += f"\n   → {step['output'][:100]}"

    # Employee's own description
    desc_section = ""
    if body.error_description:
        desc_section = f"\n--- EMPLOYEE DESCRIPTION ---\n{body.error_description}\n"

    if body.screen_text:
        desc_section += f"\nVisible screen content:\n{body.screen_text[:300]}\n"

    # Screenshot note
    screenshot_note = ""
    if body.screenshot_b64:
        screenshot_note = "\n[Screenshot of error screen is attached to this ticket]\n"

    description = f"""🤖 TED AUTO-GENERATED TICKET — Tech Express Desk Kiosk
═══════════════════════════════════════════════════
Session:   {session_id[:16]}
Employee:  {employee.get('name', 'Unknown')} ({employee.get('id', '')})
Timestamp: {timestamp}
Severity:  {severity}
AI Model:  {diagnosis.get('llm_model', 'unknown')} (confidence: {conf_pct})

--- AI DIAGNOSIS ---
{diagnosis.get('diagnosis', 'No diagnosis available')}

--- FIX STEPS ATTEMPTED ---
{steps_html or '(No steps attempted)'}
{hw_section}{sw_section}{autofix_section}{desc_section}{screenshot_note}
Device Serial: {device_serial or 'Not provided'}
Fix Key:  {diagnosis.get('fix_key', 'N/A')}
Suggested Group: {diagnosis.get('suggested_group', 'IT_SD')}
═══════════════════════════════════════════════════
Note: This ticket was created automatically by TED kiosk after the employee
reported the issue was not resolved. All diagnostic data is pre-attached.
"""
    return description


def _save_screenshot(session_id: str, screenshot_b64: str) -> Optional[str]:
    """Save the screenshot locally and return the file path."""
    if not screenshot_b64:
        return None
    try:
        reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'ted', 'reports')
        os.makedirs(os.path.normpath(reports_dir), exist_ok=True)
        filename = f"screenshot_{session_id[:8].upper()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.normpath(os.path.join(reports_dir, filename))
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(screenshot_b64 + '=='))  # pad if needed
        return filepath
    except Exception as e:
        print(f"[Ticket] Screenshot save failed: {e}")
        return None


def _generate_word_report(session_id: str, employee: dict, diagnosis: dict, body: TicketRequest) -> Optional[str]:
    """Generate a Word incident report for the ticket."""
    try:
        _autofix_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        if _autofix_path not in sys.path:
            sys.path.insert(0, _autofix_path)
        from autofix.reporter import generate_report

        hw = body.diagnostic_data.get('hardware', {})
        sw = body.diagnostic_data.get('software', {})
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "hostname": sw.get('os', {}).get('hostname', 'Unknown'),
            "platform": f"{sw.get('os', {}).get('os', '')} {sw.get('os', {}).get('release', '')}",
            "cpu":    hw.get('cpu', {"percent": 0, "cores": 0, "freq_mhz": 0}),
            "memory": hw.get('memory', {"percent": 0, "used_gb": 0, "total_gb": 0}),
            "disk":   hw.get('disk', {}).get('primary', {"percent": 0, "used_gb": 0, "total_gb": 0, "free_gb": 0}),
            "battery": hw.get('battery', {"percent": None, "plugged": None}),
            "network": [],
            "flags": body.diagnostic_data.get('hardware_flags', []),
        }
        hw_issues = body.diagnostic_data.get('issues_found', [])
        fix_results = [
            {"rule_id": s.get('label', '?'), "success": s.get('success', False),
             "method": "local", "commands_run": [], "output": s.get('output', ''), "error": None}
            for s in body.autofix_results
        ]
        reports_dir = os.path.normpath(os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..', 'ted', 'backend', 'reports'
        ))
        return generate_report(
            session_id=session_id,
            employee=employee,
            metrics=metrics,
            triggered_rules=[{"id": i, "name": i, "severity": "medium"} for i in hw_issues],
            fix_results=fix_results,
            diagnosis=diagnosis,
            outcome="ticket_created",
            output_dir=reports_dir,
        )
    except Exception as e:
        print(f"[Ticket] Word report failed: {e}")
        return None


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

    # Fetch employee
    emp_result = await db.execute(select(Employee).where(Employee.employee_id == claims["sub"]))
    employee = emp_result.scalar_one_or_none()
    employee_dict = {}
    if employee:
        employee_dict = {"id": employee.employee_id, "name": employee.display_name,
                         "email": employee.email, "freshworks_id": employee.freshworks_id}

    # Use AI diagnosis from request body (most complete) OR fall back to DB record
    if body.ai_diagnosis and body.ai_diagnosis.get('diagnosis'):
        diagnosis_dict = body.ai_diagnosis
        diagnosis_dict.setdefault('suggested_group', 'IT_SD')
    else:
        try:
            sid = _uuid.UUID(session_id)
        except ValueError:
            sid = session_id
        diag_result = await db.execute(
            select(DiagnosisResult)
            .where(cast(DiagnosisResult.session_id, String) == str(sid))
            .order_by(DiagnosisResult.created_at.desc()).limit(1)
        )
        diag = diag_result.scalar_one_or_none()
        diagnosis_dict = {
            "diagnosis": (diag.diagnosis if diag else None) or "Issue reported via TED kiosk",
            "confidence": diag.confidence if diag else 0,
            "severity":   diag.severity if diag else "medium",
            "fix_steps":  diag.fix_steps if diag else [],
            "suggested_group": "IT_SD",
        }

    # Build rich description with full context
    rich_description = _build_rich_description(
        diagnosis_dict, employee_dict, session_id, body, body.device_serial
    )

    # Save screenshot locally
    screenshot_path = _save_screenshot(session_id, body.screenshot_b64)

    # Generate Word report in background
    report_path = _generate_word_report(session_id, employee_dict, diagnosis_dict, body)

    # Inject rich description into the Freshworks payload
    diagnosis_for_fw = {**diagnosis_dict, "_rich_description": rich_description}

    # Create ticket (Freshworks or mock)
    ticket = await create_ticket(session_id, diagnosis_for_fw, employee_dict, body.device_serial)

    # Return enriched response
    return {
        **ticket,
        "screenshot_saved": bool(screenshot_path),
        "report_saved": bool(report_path),
        "report_path": os.path.basename(report_path) if report_path else None,
        "screenshot_path": os.path.basename(screenshot_path) if screenshot_path else None,
        "diagnostic_summary": {
            "issues": body.diagnostic_data.get('issues_found', []),
            "health": body.diagnostic_data.get('overall_health', 'unknown'),
        } if body.diagnostic_data else {},
    }
