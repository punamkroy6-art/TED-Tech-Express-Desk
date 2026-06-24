"""
executor.py — Local + SSH fix execution via subprocess and Paramiko
Runs auto-fix commands either locally or on a remote device over SSH.
"""

import subprocess
import platform
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("ted.autofix.executor")


def _is_browser_kill_command(cmd: str) -> bool:
    """Detect commands that would terminate browser processes on the kiosk."""
    normalized = cmd.lower()
    dangerous_markers = [
        "taskkill /f /im chrome.exe",
        "taskkill /f /im msedge.exe",
        "taskkill /f /im microsoftedgecp.exe",
        "pkill -f chrome",
        "pkill -f msedge",
        "pkill -f chromium",
        "killall chrome",
        "killall chromium",
        "killall msedge",
    ]
    return any(marker in normalized for marker in dangerous_markers)


def _sanitize_command(cmd: str) -> tuple[str, bool, str]:
    if _is_browser_kill_command(cmd):
        logger.warning("Unsafe autofix command blocked: %s", cmd)
        return (cmd, False, "Skipped unsafe browser termination command")
    return (cmd, True, "")


@dataclass
class FixResult:
    rule_id: str
    success: bool
    method: str          # 'local' | 'ssh' | 'manual'
    commands_run: list
    output: str
    error: Optional[str] = None


def run_local(rule: dict) -> FixResult:
    """Run fix commands on the local machine."""
    os_name = platform.system().lower()
    commands = rule.get("fix_commands", {}).get(os_name, [])

    if not commands:
        return FixResult(
            rule_id=rule["id"],
            success=True,
            method="manual",
            commands_run=[],
            output="No automated commands — manual steps presented to user.",
        )

    results = []
    errors = []
    skipped = []
    for cmd in commands:
        cmd, allowed, reason = _sanitize_command(cmd)
        if not allowed:
            skipped.append(f"[{cmd}] {reason}")
            continue

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            results.append(f"[{cmd}] → exit {result.returncode}")
            if result.stdout:
                results.append(result.stdout.strip()[:200])
            if result.returncode != 0 and result.stderr:
                errors.append(result.stderr.strip()[:200])
        except subprocess.TimeoutExpired:
            errors.append(f"[{cmd}] timed out after 30s")
        except Exception as e:
            errors.append(f"[{cmd}] error: {e}")

    if skipped:
        errors.extend(skipped)

    return FixResult(
        rule_id=rule["id"],
        success=len(errors) == 0,
        method="local",
        commands_run=commands,
        output="\n".join(results),
        error="\n".join(errors) if errors else None,
    )


def run_ssh(rule: dict, host: str, username: str, password: str = None,
            key_path: str = None, port: int = 22) -> FixResult:
    """Run fix commands on a remote device via SSH (Paramiko)."""
    try:
        import paramiko
    except ImportError:
        return FixResult(
            rule_id=rule["id"], success=False, method="ssh",
            commands_run=[], output="",
            error="paramiko not installed — run: pip install paramiko"
        )

    commands = rule.get("fix_commands", {}).get("ssh", [])
    if not commands:
        return FixResult(
            rule_id=rule["id"], success=True, method="manual",
            commands_run=[], output="No SSH commands defined — manual steps presented.",
        )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    results = []
    errors = []
    try:
        connect_kwargs = dict(hostname=host, port=port, username=username, timeout=10)
        if key_path:
            connect_kwargs["key_filename"] = key_path
        elif password:
            connect_kwargs["password"] = password

        client.connect(**connect_kwargs)
        for cmd in commands:
            cmd, allowed, reason = _sanitize_command(cmd)
            if not allowed:
                results.append(f"[{cmd}] skipped: {reason}")
                errors.append(reason)
                continue

            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            results.append(f"[{cmd}] → {out[:200]}")
            if err:
                errors.append(f"[{cmd}] stderr: {err[:200]}")
    except paramiko.AuthenticationException:
        errors.append("SSH authentication failed — check credentials.")
    except paramiko.SSHException as e:
        errors.append(f"SSH error: {e}")
    except Exception as e:
        errors.append(f"Connection error: {e}")
    finally:
        client.close()

    return FixResult(
        rule_id=rule["id"],
        success=len(errors) == 0,
        method="ssh",
        commands_run=commands,
        output="\n".join(results),
        error="\n".join(errors) if errors else None,
    )
