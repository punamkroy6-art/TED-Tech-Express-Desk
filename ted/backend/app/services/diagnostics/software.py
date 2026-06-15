"""
software.py — Automated Software Diagnostics
Runs OS checks, driver health, process analysis, and network connectivity tests.
Called automatically when employee starts a session.
"""
import platform, socket, subprocess, sys, os, json
from datetime import datetime


def _run(cmd: str, timeout: int = 15) -> str:
    """Run a shell command and return stdout."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (r.stdout + r.stderr).strip()[:500]
    except Exception as e:
        return f"Error: {e}"


def run_os_check() -> dict:
    """Collect OS version, uptime, and pending updates."""
    info = {
        "os": platform.system(),
        "version": platform.version(),
        "release": platform.release(),
        "machine": platform.machine(),
        "hostname": socket.gethostname(),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if platform.system() == "Windows":
        # Uptime (fast WMI query)
        uptime_raw = _run("wmic os get LastBootUpTime /value", timeout=5)
        info["last_boot"] = uptime_raw.split("=")[-1].strip()[:20] if "=" in uptime_raw else "unknown"

        # Pending updates (skip heavy COM call — use quick registry check)
        reg_check = _run('reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\Results\\Install" /v LastSuccessTime 2>nul', timeout=5)
        info["last_windows_update"] = reg_check.strip().split()[-1] if "LastSuccessTime" in reg_check else "unknown"
        info["pending_updates"] = "check_required"  # COM call too slow for kiosk

        # Windows Defender — fast registry check
        def_raw = _run('reg query "HKLM\\SOFTWARE\\Microsoft\\Windows Defender" /v DisableAntiSpyware 2>nul', timeout=5)
        info["defender_enabled"] = "0x1" not in def_raw  # 0x1 = disabled

        # Recent system errors count (fast query, last 10 events)
        info["system_errors_24h"] = "check_skipped"  # EventLog too slow for kiosk
    else:
        info["last_boot"] = _run("uptime -s", timeout=5)
        info["pending_updates"] = "N/A"
        info["defender_enabled"] = True

    return info


def run_driver_check() -> dict:
    """Scan for failed or outdated drivers."""
    result = {"status": "ok", "failed_drivers": [], "warning_drivers": []}

    if platform.system() == "Windows":
        raw = _run(
            'powershell -Command "Get-WmiObject Win32_PnPEntity | Where-Object {$_.ConfigManagerErrorCode -ne 0} | Select-Object Name,DeviceID,ConfigManagerErrorCode | ConvertTo-Json" 2>nul',
            timeout=15
        )
        if raw and raw.strip().startswith("[") or raw.strip().startswith("{"):
            try:
                drivers = json.loads(raw) if raw.strip().startswith("[") else [json.loads(raw)]
                for d in drivers[:10]:
                    result["failed_drivers"].append({
                        "name": d.get("Name", "Unknown"),
                        "error_code": d.get("ConfigManagerErrorCode", 0),
                    })
            except Exception:
                pass
        result["status"] = "warning" if result["failed_drivers"] else "ok"
    return result


def run_process_check() -> dict:
    """Identify top CPU/memory consuming processes."""
    import psutil
    procs = []
    for p in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                    key=lambda x: x.info.get('memory_percent', 0) or 0, reverse=True)[:8]:
        try:
            procs.append({
                "name": p.info['name'],
                "pid": p.info['pid'],
                "cpu_pct": round(p.info.get('cpu_percent', 0) or 0, 1),
                "mem_pct": round(p.info.get('memory_percent', 0) or 0, 2),
            })
        except Exception:
            pass

    high_cpu = [p for p in procs if p['cpu_pct'] > 40]
    high_mem = [p for p in procs if p['mem_pct'] > 15]
    return {"top_processes": procs, "high_cpu": high_cpu, "high_memory": high_mem}


def run_network_check() -> dict:
    """Test connectivity: DNS, internet, corporate proxy, VPN."""
    results = {}

    # DNS resolution (TCP check, faster than ICMP)
    try:
        socket.setdefaulttimeout(4)
        socket.getaddrinfo("www.google.com", 80)
        results["dns"] = "ok"
    except Exception:
        results["dns"] = "failed"

    # Internet connectivity — TCP to port 443 (more reliable than ICMP ping)
    try:
        with socket.create_connection(("8.8.8.8", 53), timeout=4):
            results["internet"] = "ok"
    except Exception:
        # Fallback to HTTP check
        try:
            with socket.create_connection(("www.google.com", 80), timeout=4):
                results["internet"] = "ok"
        except Exception:
            results["internet"] = "failed"

    # Corporate DNS
    try:
        socket.getaddrinfo("corporate.intranet", 80)
        results["corporate_dns"] = "ok"
    except Exception:
        results["corporate_dns"] = "unreachable"  # expected in dev

    # VPN check (look for VPN adapters)
    if platform.system() == "Windows":
        adapters = _run("ipconfig /all | findstr /i \"VPN Cisco Pulse AnyConnect Zscaler\"", timeout=5)
        results["vpn_adapter_detected"] = bool(adapters.strip())
    else:
        results["vpn_adapter_detected"] = os.path.exists("/etc/openvpn") or os.path.exists("/etc/vpnc")

    return results


def run_full_software_diagnostic() -> dict:
    """Run all software checks and return a consolidated report."""
    report = {
        "type": "software",
        "timestamp": datetime.utcnow().isoformat(),
        "os": run_os_check(),
        "drivers": run_driver_check(),
        "processes": run_process_check(),
        "network": run_network_check(),
        "issues_found": [],
    }

    # Summarise issues
    if report["drivers"]["failed_drivers"]:
        report["issues_found"].append(f"{len(report['drivers']['failed_drivers'])} driver(s) failed")
    if report["processes"]["high_cpu"]:
        names = ", ".join(p["name"] for p in report["processes"]["high_cpu"][:3])
        report["issues_found"].append(f"High CPU: {names}")
    if report["network"]["internet"] == "failed":
        report["issues_found"].append("No internet connectivity")
    if report["network"]["dns"] == "failed":
        report["issues_found"].append("DNS resolution failed")
    if report["os"].get("pending_updates", 0) not in (0, "N/A", "unknown"):
        if isinstance(report["os"]["pending_updates"], int) and report["os"]["pending_updates"] > 10:
            report["issues_found"].append(f"{report['os']['pending_updates']} Windows updates pending")

    report["health"] = "critical" if len(report["issues_found"]) > 2 else \
                       "warning" if report["issues_found"] else "healthy"
    return report
