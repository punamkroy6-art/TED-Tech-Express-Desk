import sys
import os
import asyncio
import uuid
from datetime import datetime

# Resolve sys.path so we can import app models and database configuration directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, AsyncSessionLocal, USE_LOCAL_MOCK
from app.models.employee import Employee
from app.models.error_pattern import ErrorPattern
from app.models.session import Session
from app.models.diagnosis import DiagnosisResult
from app.models.audit_log import AuditLog

async def seed_database():
    print(f"[{datetime.now()}] Initializing local database schema...")
    # 1. Create tables if they do not exist
    await init_db()
    print("Database tables initialized successfully!")

    print(f"[{datetime.now()}] Seeding synthetic database records...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 2. Add Synthetic Employees
            employees = [
                Employee(
                    employee_id="EMP-1029",
                    display_name="Alice Vance",
                    email="alice.vance@company.com",
                    department="Engineering",
                    manager_email="carol.manager@company.com",
                    freshworks_id="fw-req-8891",
                    last_seen=datetime.utcnow()
                ),
                Employee(
                    employee_id="EMP-4552",
                    display_name="Bob Miller",
                    email="bob.miller@company.com",
                    department="Sales",
                    manager_email="carol.manager@company.com",
                    freshworks_id="fw-req-7762",
                    last_seen=datetime.utcnow()
                ),
                Employee(
                    employee_id="EMP-9003",
                    display_name="Charlie Green",
                    email="charlie.green@company.com",
                    department="HR",
                    manager_email="david.hr.dir@company.com",
                    freshworks_id="fw-req-2234",
                    last_seen=datetime.utcnow()
                )
            ]
            session.add_all(employees)
            print(f"- Queued {len(employees)} synthetic employees")

            # 3. Add Synthetic Error Patterns
            error_patterns = [
                ErrorPattern(
                    error_code="0x000000D1",
                    keywords=["blue screen", "bsod", "driver_irql", "crash"],
                    os_platform="windows",
                    category="bsod",
                    severity="critical",
                    description="Driver IRQL not less or equal (Blue Screen of Death / BSOD)",
                    fix_steps=[
                        {"step": 1, "instruction": "Reboot your computer into Safe Mode."},
                        {"step": 2, "instruction": "Uninstall the recently installed third-party graphics/network drivers."},
                        {"step": 3, "instruction": "Run 'Windows Memory Diagnostic' tool to check RAM health."},
                        {"step": 4, "instruction": "Restart normally and check for stability."}
                    ],
                    estimated_mins=15,
                    success_rate=0.89,
                    source="manual",
                    is_active=True
                ),
                ErrorPattern(
                    error_code="OKTA-403-MFA",
                    keywords=["okta", "login", "sso", "mfa", "auth", "lockout"],
                    os_platform="any",
                    category="auth",
                    severity="medium",
                    description="Okta Multi-Factor Authentication Push Lockout or Token Expired",
                    fix_steps=[
                        {"step": 1, "instruction": "Clear browser cache and cookies entirely."},
                        {"step": 2, "instruction": "Ensure Okta Verify app on your phone is open and connected to Wi-Fi."},
                        {"step": 3, "instruction": "If push fails, click 'Or enter passcode' and input the numeric code from the app."},
                        {"step": 4, "instruction": "If account is locked, wait 15 minutes or trigger an automated email unlock."}
                    ],
                    estimated_mins=5,
                    success_rate=0.96,
                    source="manual",
                    is_active=True
                ),
                ErrorPattern(
                    error_code="VPN-TUN-500",
                    keywords=["vpn", "pulse secure", "tunnel", "disconnect", "network"],
                    os_platform="any",
                    category="network",
                    severity="high",
                    description="Corporate VPN Tunnel Connection Failure or Gateway Timeout",
                    fix_steps=[
                        {"step": 1, "instruction": "Disconnect from corporate VPN client manually."},
                        {"step": 2, "instruction": "Disconnect and reconnect to your local Wi-Fi router."},
                        {"step": 3, "instruction": "Ensure you are NOT connected to any public VPN clients."},
                        {"step": 4, "instruction": "Re-launch corporate VPN and log in using your SSO badge credential."}
                    ],
                    estimated_mins=8,
                    success_rate=0.92,
                    source="manual",
                    is_active=True
                ),
                ErrorPattern(
                    error_code="PRINT-OFFLINE",
                    keywords=["printer", "print", "printing", "offline", "queue", "stuck"],
                    os_platform="windows",
                    category="peripheral",
                    severity="low",
                    description="Printer is offline or print queue is stuck",
                    fix_steps=[
                        "Open Settings > Bluetooth & devices > Printers & scanners.",
                        "Click your printer and select 'Open print queue'.",
                        "Cancel all pending jobs in the queue.",
                        "Right-click the printer and select 'See what's printing', then choose Printer > Use Printer Online.",
                        "Restart the printer and try printing a test page."
                    ],
                    estimated_mins=5,
                    success_rate=0.91,
                    source="manual",
                    is_active=True
                ),
                ErrorPattern(
                    error_code="TEAMS-AUDIO",
                    keywords=["teams", "meeting", "video", "call", "dropping", "freezing", "audio", "camera", "microphone"],
                    os_platform="any",
                    category="application",
                    severity="medium",
                    description="Microsoft Teams audio, video, or call quality issues",
                    fix_steps=[
                        "Close Teams completely and reopen it.",
                        "Go to Teams Settings > Devices and re-select your microphone, speaker, and camera.",
                        "Check your internet connection — Teams needs at least 1.5 Mbps.",
                        "Clear the Teams cache: close Teams, press Win+R, type %AppData%\\Microsoft\\Teams, delete all files in the Cache folder.",
                        "Restart Teams and test with a test call."
                    ],
                    estimated_mins=8,
                    success_rate=0.87,
                    source="manual",
                    is_active=True
                ),
                ErrorPattern(
                    error_code="OUTLOOK-SYNC",
                    keywords=["outlook", "email", "sync", "syncing", "calendar", "not sending", "stuck", "loading"],
                    os_platform="windows",
                    category="application",
                    severity="medium",
                    description="Outlook email or calendar not syncing or loading",
                    fix_steps=[
                        "Close Outlook and reopen it.",
                        "Check your internet connection and VPN status.",
                        "Go to File > Account Settings > Account Settings, select your email account and click Repair.",
                        "If issue persists, go to File > Options > Advanced > Send/Receive and click Send/Receive All Folders.",
                        "Restart your device and open Outlook again."
                    ],
                    estimated_mins=7,
                    success_rate=0.89,
                    source="manual",
                    is_active=True
                ),
                ErrorPattern(
                    error_code="DISK-FULL",
                    keywords=["disk", "storage", "space", "full", "low", "drive", "c drive", "no space"],
                    os_platform="windows",
                    category="storage",
                    severity="high",
                    description="Low disk space on system drive",
                    fix_steps=[
                        "Open Settings > System > Storage to see what is using space.",
                        "Click 'Temporary files' and delete files you don't need.",
                        "Empty the Recycle Bin by right-clicking it on the desktop.",
                        "Run Disk Cleanup: press Win+S, search 'Disk Cleanup', and run it on the C: drive.",
                        "If still low, contact IT to archive old files or expand storage."
                    ],
                    estimated_mins=10,
                    success_rate=0.93,
                    source="manual",
                    is_active=True
                ),
                ErrorPattern(
                    error_code="WIFI-SLOW",
                    keywords=["wifi", "wi-fi", "wireless", "slow", "internet", "network", "disconnect", "connection", "dropping"],
                    os_platform="any",
                    category="network",
                    severity="medium",
                    description="Slow or unstable Wi-Fi / network connection",
                    fix_steps=[
                        "Click the Wi-Fi icon in the taskbar, disconnect, and reconnect to the corporate network.",
                        "If still slow, forget the network and rejoin: Settings > Network & Internet > Wi-Fi > Manage known networks.",
                        "Move closer to a Wi-Fi access point if possible.",
                        "Run the network troubleshooter: Settings > System > Troubleshoot > Other troubleshooters > Internet Connections.",
                        "If issue persists, contact IT — there may be an access point outage in your area."
                    ],
                    estimated_mins=6,
                    success_rate=0.85,
                    source="manual",
                    is_active=True
                ),
            ]
            session.add_all(error_patterns)
            print(f"- Queued {len(error_patterns)} synthetic error patterns")

            # 4. Add a Synthetic Kiosk Session
            # We generate a deterministic UUID so we can easily link child records
            session_uuid = uuid.UUID("3f8c85fa-7d4e-4f7f-a63e-001122334455")
            kiosk_session = Session(
                id=session_uuid,
                employee_id="EMP-1029", # Alice Vance
                kiosk_id="KIOSK-BOS-03",
                started_at=datetime.utcnow(),
                auth_method="badge",
                issue_type="software",
                outcome="resolved",
                ticket_id=None,
                csat_score=5
            )
            session.add(kiosk_session)
            print(f"- Queued synthetic kiosk session (ID: {session_uuid})")

            # 5. Add Synthetic AI Diagnosis Result
            diag_uuid = uuid.UUID("8f7a6b5c-4d3e-2f1a-0b9c-d8e7f6a5b4c3")
            diagnosis = DiagnosisResult(
                id=diag_uuid,
                session_id=session_uuid,
                run_number=1,
                input_error_text="I got a blue screen crash while opening CAD software",
                input_device_info={"os": "Windows 11", "model": "Dell Precision 5570", "ram_gb": 32},
                ocr_output={"text_extracted": "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED (0x0000007E)"},
                diagnosis="System thread exception crash triggered by graphics driver incompatibility.",
                confidence=0.88,
                severity="critical",
                fix_steps=["Boot in Safe Mode", "Update NVIDIA Graphics Driver", "Run System File Checker SFC /scannow"],
                kb_references=[{"id": "KB-121", "title": "Resolving Windows 11 BSOD on Dell laptops", "url": "https://company.service.com/kb/121"}],
                past_ticket_refs=[{"id": "INC-88219", "summary": "BSOD on Dell 5570", "resolution": "Updated driver"}],
                suggested_group="IT_Desktop_Support",
                action_taken="self_resolve",
                llm_model="llama-3.3-70b-versatile",
                llm_tokens_used=420,
                processing_ms=1850
            )
            session.add(diagnosis)
            print(f"- Queued synthetic AI diagnosis result (ID: {diag_uuid})")

            # 6. Add Synthetic Audit Log
            audit_log = AuditLog(
                session_id=session_uuid,
                actor="EMP-1029",
                action="SESSION_START",
                detail={"auth_method": "badge", "kiosk_id": "KIOSK-BOS-03"},
                ip_address="192.168.12.110"
            )
            session.add(audit_log)
            print(f"- Queued synthetic audit event logs")

    print(f"[{datetime.now()}] Seed transaction COMMITTED successfully!")
    print("Database seeding completed.")

if __name__ == "__main__":
    if not USE_LOCAL_MOCK:
        print("[WARNING] USE_LOCAL_MOCK is set to False. Seeding will run against production PostgreSQL.")
    asyncio.run(seed_database())
