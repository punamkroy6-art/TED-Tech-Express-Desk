"""
/api/autofix — Job-based IoT Auto-Fix (permanent browser-crash fix)

Architecture: Fire-and-forget + polling
  POST /autofix/start  → starts job in background thread, returns job_id INSTANTLY
  GET  /autofix/status/{job_id} → frontend polls every 1s, gets live step updates

Why: Holding an HTTP connection open for 30s while subprocess runs crashes browsers.
     Short poll responses (< 100ms each) never crash anything.
"""
import sys, os, uuid, threading, platform, subprocess, time
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.services import auth_service

router = APIRouter()

# In-memory job store (TTL cleanup happens on each request)
_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()
JOB_TTL = 300  # seconds before a completed job is removed


# ── Models ────────────────────────────────────────────────────────────────────

class StartRequest(BaseModel):
    fix_key: str
    ssh_host: str = ""
    ssh_user: str = ""
    ssh_password: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_cmd(cmd: str, timeout: int = 8) -> tuple[bool, str]:
    """Run a shell command. Hard-capped at `timeout` seconds."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=timeout,
            encoding="utf-8", errors="replace"
        )
        out = (r.stdout + r.stderr).strip()[:300] or "Command completed"
        return r.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, f"Timed out after {timeout}s"
    except Exception as e:
        return False, f"Error: {str(e)[:80]}"


def _load_config(fix_key: str) -> Optional[dict]:
    try:
        import yaml
        cfg_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "autofix", "config.yaml")
        )
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f)
        return cfg.get("ai_fixes", {}).get(fix_key.upper())
    except Exception:
        return None


def _cleanup_old_jobs():
    """Remove jobs older than JOB_TTL seconds."""
    now = time.time()
    with _JOBS_LOCK:
        stale = [jid for jid, job in _JOBS.items()
                 if now - job.get("created_at", now) > JOB_TTL]
        for jid in stale:
            del _JOBS[jid]


def _run_job(job_id: str, fix_def: dict, ssh_host: str, ssh_user: str, ssh_password: str):
    """Background thread: execute each step and update job state."""
    os_name = platform.system().lower()
    MAX_STEP = 8   # hard cap per step in seconds

    steps = fix_def.get("steps", [])
    use_ssh = bool(ssh_host and ssh_user)

    for i, step in enumerate(steps):
        label = step.get("label", f"Step {i+1}")
        timeout = min(step.get("timeout", 8), MAX_STEP)

        # Mark step as running
        with _JOBS_LOCK:
            _JOBS[job_id]["steps"][i]["status"] = "running"
            _JOBS[job_id]["current_step"] = i

        if use_ssh:
            cmd = step.get("command_ssh", "echo skipped")
            try:
                import paramiko
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=ssh_host, username=ssh_user,
                               password=ssh_password, timeout=8)
                _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
                out = (stdout.read().decode("utf-8", errors="replace") +
                       stderr.read().decode("utf-8", errors="replace")).strip()[:300]
                client.close()
                ok = True
            except Exception as e:
                ok, out = False, f"SSH error: {str(e)[:80]}"
        else:
            cmd_key = f"command_{os_name}" if os_name in ("windows", "linux", "darwin") else "command_windows"
            cmd = step.get(cmd_key) or step.get("command_windows", "echo not supported")
            ok, out = _run_cmd(cmd, timeout)

        duration_ms = int(time.time() * 1000)

        with _JOBS_LOCK:
            _JOBS[job_id]["steps"][i].update({
                "status": "done" if ok else "failed",
                "success": ok,
                "output": out,
                "duration_ms": duration_ms,
            })

    # Mark job complete
    with _JOBS_LOCK:
        job = _JOBS[job_id]
        passed = sum(1 for s in job["steps"] if s.get("success"))
        total = len(job["steps"])
        job["done"] = True
        job["overall_success"] = passed > 0
        job["summary"] = (
            f"Auto-fix completed — {passed}/{total} steps succeeded. Issue should be resolved."
            if passed > 0 else
            f"Auto-fix attempted — 0/{total} steps succeeded. A ticket will be raised."
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/autofix/start")
async def start_autofix(body: StartRequest, authorization: str = Header(...)):
    """
    Start an auto-fix job. Returns job_id IMMEDIATELY (no waiting).
    The job runs in a background thread.
    Frontend polls /autofix/status/{job_id} every 1 second for updates.
    """
    token = authorization.removeprefix("Bearer ").strip()
    try:
        auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    fix_def = _load_config(body.fix_key)
    if not fix_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No auto-fix defined for: {body.fix_key}"
        )

    _cleanup_old_jobs()

    job_id = str(uuid.uuid4())[:12]
    steps_init = [
        {"label": s.get("label", f"Step {i+1}"), "status": "pending",
         "success": False, "output": "", "duration_ms": 0}
        for i, s in enumerate(fix_def.get("steps", []))
    ]

    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "fix_key": body.fix_key,
            "fix_name": fix_def.get("name", body.fix_key),
            "done": False,
            "overall_success": False,
            "current_step": -1,
            "steps": steps_init,
            "summary": "",
            "created_at": time.time(),
        }

    # Start background thread — returns instantly
    t = threading.Thread(
        target=_run_job,
        args=(job_id, fix_def, body.ssh_host, body.ssh_user, body.ssh_password),
        daemon=True,
    )
    t.start()

    return {"job_id": job_id, "fix_name": fix_def.get("name"), "total_steps": len(steps_init)}


@router.get("/autofix/status/{job_id}")
async def get_autofix_status(job_id: str, authorization: str = Header(...)):
    """
    Poll job status. Returns current step progress.
    Frontend calls this every 1 second until done=true.
    Response is always fast (< 10ms) — no subprocess blocking.
    """
    token = authorization.removeprefix("Bearer ").strip()
    try:
        auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    with _JOBS_LOCK:
        job = _JOBS.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")

    return job


@router.post("/autofix/run")
async def run_autofix_legacy(body: StartRequest, authorization: str = Header(...)):
    """
    Legacy sync endpoint kept for backward compat.
    Now internally uses the job system with a short poll loop.
    Max wait: 25s. If job not done, returns partial results.
    """
    token = authorization.removeprefix("Bearer ").strip()
    try:
        auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Start job
    fix_def = _load_config(body.fix_key)
    if not fix_def:
        raise HTTPException(status_code=404, detail=f"No fix for: {body.fix_key}")

    job_id = str(uuid.uuid4())[:12]
    steps_init = [
        {"label": s.get("label", f"Step {i+1}"), "status": "pending",
         "success": False, "output": "", "duration_ms": 0}
        for i, s in enumerate(fix_def.get("steps", []))
    ]
    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "job_id": job_id, "fix_key": body.fix_key,
            "fix_name": fix_def.get("name", body.fix_key),
            "done": False, "overall_success": False,
            "current_step": -1, "steps": steps_init,
            "summary": "", "created_at": time.time(),
        }

    import asyncio
    loop = asyncio.get_event_loop()
    t = threading.Thread(target=_run_job,
                         args=(job_id, fix_def, body.ssh_host, body.ssh_user, body.ssh_password),
                         daemon=True)
    t.start()

    # Poll up to 24s (3 steps × 8s max)
    for _ in range(24):
        await asyncio.sleep(1)
        with _JOBS_LOCK:
            job = _JOBS.get(job_id, {})
        if job.get("done"):
            break

    with _JOBS_LOCK:
        job = _JOBS.get(job_id, {})

    passed = sum(1 for s in job.get("steps", []) if s.get("success"))
    total = len(job.get("steps", []))

    return {
        "fix_key": body.fix_key,
        "fix_name": job.get("fix_name", body.fix_key),
        "overall_success": passed > 0,
        "steps": job.get("steps", []),
        "summary": job.get("summary") or f"Auto-fix completed — {passed}/{total} steps succeeded.",
    }
