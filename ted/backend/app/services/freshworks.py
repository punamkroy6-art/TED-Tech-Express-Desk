import httpx, asyncio, json, base64
from app.config import settings


def _get_base_url() -> str:
    return f"https://{settings.freshworks_domain}/api/v2" if settings.freshworks_domain else ""


def _get_headers() -> dict:
    """
    Freshservice Basic Auth = base64(api_key:X)
    Accepts raw API key — encodes it automatically.
    """
    key = settings.freshworks_api_key.strip()
    # Always encode as base64(key:X) — Freshservice standard
    encoded = base64.b64encode(f"{key}:X".encode()).decode()
    return {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded}",
    }


async def create_ticket(session_id: str, diagnosis: dict, employee: dict, device_serial: str = "") -> dict:
    if not settings.freshworks_domain or not settings.freshworks_api_key:
        # Return a mock ticket when Freshworks is not configured
        mock_id = f"TED-{session_id[:8].upper()}"
        return {"ticket_id": mock_id, "status": "mock", "url": f"#ticket/{mock_id}"}

    # Build payload — use email as fallback if freshworks_id not set
    payload = {
        "subject": f"[TED] {diagnosis.get('diagnosis', 'IT Issue')[:80]}",
        "description": _build_description(diagnosis, device_serial),
        "priority": _severity_to_priority(diagnosis.get("severity", "medium")),
        "status": 2,  # Open
    }
    # Requester: use freshworks_id if available, else fall back to email
    if employee.get("freshworks_id"):
        payload["requester_id"] = int(employee["freshworks_id"])
    elif employee.get("email"):
        payload["email"] = employee["email"]

    # Add custom fields if they exist in your Freshservice schema
    # Uncomment and map to your actual field names:
    # payload["custom_fields"] = {
    #     "cf_kiosk_session_id": session_id,
    #     "cf_ai_confidence": str(round(diagnosis.get("confidence", 0) * 100)) + "%",
    #     "cf_device_serial": device_serial,
    # }

    return await _post_with_retry("/tickets", payload)


async def _post_with_retry(endpoint: str, payload: dict, retries: int = 3) -> dict:
    delay = 2
    base_url = _get_base_url()
    headers = _get_headers()
    async with httpx.AsyncClient(timeout=15) as client:
        for attempt in range(retries):
            try:
                r = await client.post(f"{base_url}{endpoint}", headers=headers, json=payload)
                if r.status_code == 429:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                r.raise_for_status()
                data = r.json()
                ticket = data.get("ticket", {})
                ticket_id = str(ticket.get("id", ""))
                ticket_url = f"https://{settings.freshworks_domain}/helpdesk/tickets/{ticket_id}"
                return {
                    "ticket_id": f"FS-{ticket_id}",
                    "status": "created",
                    "url": ticket_url,
                    "freshservice_id": ticket_id,
                }
            except httpx.HTTPStatusError as e:
                if attempt == retries - 1:
                    # Return degraded mock so user flow doesn't break
                    mock_id = f"TED-OFFLINE-{session_id[:6].upper() if 'session_id' in dir() else 'ERR'}"
                    return {"ticket_id": mock_id, "status": "offline", "error": str(e)}
                await asyncio.sleep(delay)
                delay *= 2
    raise RuntimeError("Failed to create Freshworks ticket after retries")


def _severity_to_priority(severity: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(severity, 2)


def _build_description(diagnosis: dict, serial: str) -> str:
    steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(diagnosis.get("fix_steps", [])))
    return (
        f"AI Diagnosis: {diagnosis.get('diagnosis', '')}\n\n"
        f"Fix Steps Attempted:\n{steps}\n\n"
        f"Device Serial: {serial}\n"
        f"AI Confidence: {diagnosis.get('confidence', 0):.0%}"
    )
