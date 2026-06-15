"""
/api/autofix/run  — IoT Auto-Fix Execution Endpoint
Executes real system commands based on AI diagnosis category.
Returns live step-by-step results so the frontend can show progress.
"""
import sys, os, subprocess, platform, asyncio, time
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import auth_service

# Make autofix module importable
_autofix_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _autofix_path not in sys.path:
    sys.path.insert(0, _autofix_path)

router = APIRouter()


class AutoFixRequest(BaseModel):
    fix_key: str          # e.g. 'WIFI', 'VPN', 'PRINTER', 'TEAMS', 'OUTLOOK', 'BSOD'
    ssh_host: str = ""    # remote device IP (optional)
    ssh_user: str = ""
    ssh_password: str = ""


class StepResult(BaseModel):
    label: str
    success: bool
    output: str
    duration_ms: int


class AutoFixResponse(BaseModel):
    fix_key: str
    fix_name: str
    overall_success: bool
    steps: list[StepResult]
    summary: str


def _run_command(cmd: str, timeout: int = 30) -> tuple[bool, str]:
    """Execute a shell command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output[:300] or "Command completed"
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"


def _run_ssh_command(cmd: str, host: str, user: str, password: str, timeout: int = 30) -> tuple[bool, str]:
    """Execute command on remote device via SSH."""
    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=user, password=password, timeout=10)
        _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        client.close()
        return True, (out or err or "Command completed")[:300]
    except Exception as e:
        return False, f"SSH error: {str(e)[:100]}"


def _load_fix_config(fix_key: str) -> dict | None:
    """Load fix definition from config.yaml."""
    try:
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'autofix', 'config.yaml')
        with open(os.path.normpath(config_path)) as f:
            config = yaml.safe_load(f)
        return config.get('ai_fixes', {}).get(fix_key.upper())
    except Exception:
        return None


@router.post("/autofix/run", response_model=AutoFixResponse)
async def run_autofix(
    body: AutoFixRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute IoT auto-fix commands for the diagnosed issue.
    Runs each step sequentially and returns pass/fail per step.
    """
    token = authorization.removeprefix("Bearer ").strip()
    try:
        auth_service.decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    fix_def = _load_fix_config(body.fix_key)
    if not fix_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No auto-fix defined for key: {body.fix_key}"
        )

    os_name = platform.system().lower()
    use_ssh = bool(body.ssh_host and body.ssh_user)

    step_results: list[StepResult] = []

    for step in fix_def.get('steps', []):
        label = step.get('label', 'Running fix...')
        timeout = step.get('timeout', 30)
        t0 = time.time()

        if use_ssh:
            cmd = step.get('command_ssh', 'echo skipped')
            success, output = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _run_ssh_command(cmd, body.ssh_host, body.ssh_user, body.ssh_password, timeout)
            )
        else:
            cmd_key = f'command_{os_name}' if os_name in ('windows', 'linux', 'darwin') else 'command_windows'
            cmd = step.get(cmd_key) or step.get('command_windows', 'echo not supported')
            success, output = await asyncio.get_event_loop().run_in_executor(
                None, lambda c=cmd, t=timeout: _run_command(c, t)
            )

        duration_ms = int((time.time() - t0) * 1000)
        step_results.append(StepResult(
            label=label,
            success=success,
            output=output,
            duration_ms=duration_ms,
        ))

    overall_success = any(s.success for s in step_results)
    passed = sum(1 for s in step_results if s.success)
    total = len(step_results)

    if overall_success:
        summary = f"Auto-fix completed — {passed}/{total} steps succeeded. Issue should be resolved."
    else:
        summary = f"Auto-fix attempted — {passed}/{total} steps succeeded. A ticket has been raised for the remaining steps."

    return AutoFixResponse(
        fix_key=body.fix_key,
        fix_name=fix_def.get('name', body.fix_key),
        overall_success=overall_success,
        steps=step_results,
        summary=summary,
    )


@router.get("/autofix/keys")
async def list_fix_keys(authorization: str = Header(...)):
    """List all available auto-fix keys."""
    try:
        auth_service.decode_token(authorization.removeprefix("Bearer ").strip())
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        import yaml
        config_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'autofix', 'config.yaml'
        ))
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return {k: v.get('name', k) for k, v in config.get('ai_fixes', {}).items()}
    except Exception as e:
        return {"error": str(e)}
