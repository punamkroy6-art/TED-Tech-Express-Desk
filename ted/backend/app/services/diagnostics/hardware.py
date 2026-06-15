"""
hardware.py — Automated Hardware Diagnostics
Uses psutil + WMI/system commands to check CPU, RAM, disk, battery, USB devices.
"""
import platform, subprocess, json
import psutil
from datetime import datetime


def _run(cmd: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (r.stdout + r.stderr).strip()[:500]
    except Exception as e:
        return f"Error: {e}"


def run_cpu_check() -> dict:
    freq = psutil.cpu_freq()
    return {
        "percent": psutil.cpu_percent(interval=1),
        "cores_logical": psutil.cpu_count(logical=True),
        "cores_physical": psutil.cpu_count(logical=False),
        "freq_mhz": round(freq.current, 1) if freq else None,
        "freq_max_mhz": round(freq.max, 1) if freq else None,
        "status": "warning" if psutil.cpu_percent(interval=0.5) > 85 else "ok",
    }


def run_memory_check() -> dict:
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_gb": round(mem.total / 1e9, 2),
        "used_gb": round(mem.used / 1e9, 2),
        "available_gb": round(mem.available / 1e9, 2),
        "percent": mem.percent,
        "swap_total_gb": round(swap.total / 1e9, 2),
        "swap_used_gb": round(swap.used / 1e9, 2),
        "status": "critical" if mem.percent > 95 else "warning" if mem.percent > 85 else "ok",
    }


def run_disk_check() -> dict:
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "filesystem": part.fstype,
                "total_gb": round(usage.total / 1e9, 2),
                "used_gb": round(usage.used / 1e9, 2),
                "free_gb": round(usage.free / 1e9, 2),
                "percent": usage.percent,
                "status": "critical" if usage.percent > 92 else "warning" if usage.percent > 80 else "ok",
            })
        except Exception:
            pass
    primary = disks[0] if disks else {}
    return {"drives": disks, "primary": primary,
            "overall": "critical" if any(d["status"] == "critical" for d in disks) else
                       "warning" if any(d["status"] == "warning" for d in disks) else "ok"}


def run_battery_check() -> dict:
    battery = psutil.sensors_battery()
    if not battery:
        return {"present": False, "type": "desktop", "status": "ok"}
    return {
        "present": True,
        "percent": round(battery.percent, 1),
        "plugged": battery.power_plugged,
        "seconds_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else -1,
        "status": "critical" if battery.percent < 10 and not battery.power_plugged else
                  "warning" if battery.percent < 20 and not battery.power_plugged else "ok",
    }


def run_usb_check() -> dict:
    """List connected USB devices."""
    devices = []
    if platform.system() == "Windows":
        raw = _run(
            'powershell -Command "Get-WmiObject Win32_USBHub | Select-Object Name,DeviceID | ConvertTo-Json" 2>nul',
            timeout=8
        )
        if raw and (raw.strip().startswith("[") or raw.strip().startswith("{")):
            try:
                items = json.loads(raw) if raw.strip().startswith("[") else [json.loads(raw)]
                devices = [{"name": d.get("Name", "Unknown"), "id": d.get("DeviceID", "")} for d in items[:10]]
            except Exception:
                pass
    elif platform.system() == "Linux":
        raw = _run("lsusb 2>/dev/null", timeout=5)
        devices = [{"name": line.split("ID")[1].strip() if "ID" in line else line} for line in raw.splitlines()[:10]]

    return {"count": len(devices), "devices": devices,
            "status": "ok" if devices else "no_devices"}


def run_screen_check() -> dict:
    """Check screen/display health."""
    if platform.system() == "Windows":
        raw = _run(
            'powershell -Command "Get-WmiObject Win32_VideoController | Select-Object Name,CurrentHorizontalResolution,CurrentVerticalResolution,AdapterRAM | ConvertTo-Json" 2>nul',
            timeout=8
        )
        try:
            d = json.loads(raw) if raw.strip().startswith("{") else (json.loads(raw)[0] if raw.strip().startswith("[") else {})
            return {
                "adapter": d.get("Name", "Unknown"),
                "resolution": f"{d.get('CurrentHorizontalResolution','?')}x{d.get('CurrentVerticalResolution','?')}",
                "vram_mb": round(int(d.get("AdapterRAM", 0)) / 1e6, 0) if d.get("AdapterRAM") else "?",
                "status": "ok",
            }
        except Exception:
            pass
    return {"status": "unknown"}


def run_thermal_check() -> dict:
    """Check temperatures (where available)."""
    temps = {}
    try:
        sensors = psutil.sensors_temperatures()
        for name, entries in sensors.items():
            for e in entries:
                if e.current and e.current > 0:
                    temps[f"{name}/{e.label or 'core'}"] = {
                        "celsius": round(e.current, 1),
                        "high": e.high,
                        "critical": e.critical,
                        "status": "critical" if e.critical and e.current >= e.critical else
                                  "warning" if e.high and e.current >= e.high else "ok",
                    }
    except AttributeError:
        pass  # Not available on all platforms
    return {"sensors": temps, "available": bool(temps)}


def run_full_hardware_diagnostic() -> dict:
    """Run all hardware checks and return consolidated report."""
    report = {
        "type": "hardware",
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": run_cpu_check(),
        "memory": run_memory_check(),
        "disk": run_disk_check(),
        "battery": run_battery_check(),
        "usb": run_usb_check(),
        "display": run_screen_check(),
        "thermal": run_thermal_check(),
        "issues_found": [],
    }

    # Consolidate issues
    if report["cpu"]["status"] != "ok":
        report["issues_found"].append(f"High CPU: {report['cpu']['percent']}%")
    if report["memory"]["status"] != "ok":
        report["issues_found"].append(f"High RAM: {report['memory']['percent']}%")
    if report["disk"]["overall"] != "ok":
        for d in report["disk"]["drives"]:
            if d["status"] != "ok":
                report["issues_found"].append(f"Low disk on {d['mountpoint']}: {d['free_gb']} GB free")
    if report["battery"]["status"] != "ok":
        report["issues_found"].append(f"Low battery: {report['battery']['percent']}%")
    for sensor, data in report["thermal"].get("sensors", {}).items():
        if data.get("status") == "critical":
            report["issues_found"].append(f"Thermal critical: {sensor} at {data['celsius']}°C")

    report["health"] = "critical" if len(report["issues_found"]) > 2 else \
                       "warning" if report["issues_found"] else "healthy"
    return report
