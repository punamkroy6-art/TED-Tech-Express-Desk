"""
diagnostics.py — Hardware metrics collection via psutil
Reads CPU, RAM, disk, battery and network stats from the local machine.
"""

import psutil
import platform
import socket
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HardwareMetrics:
    timestamp: str
    hostname: str
    platform: str

    # CPU
    cpu_percent: float
    cpu_count: int
    cpu_freq_mhz: Optional[float]

    # Memory
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float

    # Disk (primary drive)
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    disk_free_gb: float

    # Battery (None if desktop)
    battery_percent: Optional[float]
    battery_plugged: Optional[bool]

    # Network
    network_interfaces: list = field(default_factory=list)

    # Flagged issues (populated by engine)
    flags: list = field(default_factory=list)


def collect() -> HardwareMetrics:
    """Collect all hardware metrics from the local device."""
    cpu_freq = psutil.cpu_freq()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\" if platform.system() == "Windows" else "/")
    battery = psutil.sensors_battery()

    # Network interfaces
    net_addrs = psutil.net_if_addrs()
    interfaces = [
        {"name": name, "address": addrs[0].address if addrs else "unknown"}
        for name, addrs in net_addrs.items()
        if name not in ("lo", "Loopback Pseudo-Interface 1")
    ]

    return HardwareMetrics(
        timestamp=datetime.utcnow().isoformat(),
        hostname=socket.gethostname(),
        platform=f"{platform.system()} {platform.release()}",
        cpu_percent=psutil.cpu_percent(interval=1),
        cpu_count=psutil.cpu_count(logical=True),
        cpu_freq_mhz=round(cpu_freq.current, 1) if cpu_freq else None,
        memory_percent=mem.percent,
        memory_used_gb=round(mem.used / 1e9, 2),
        memory_total_gb=round(mem.total / 1e9, 2),
        disk_percent=disk.percent,
        disk_used_gb=round(disk.used / 1e9, 2),
        disk_total_gb=round(disk.total / 1e9, 2),
        disk_free_gb=round(disk.free / 1e9, 2),
        battery_percent=battery.percent if battery else None,
        battery_plugged=battery.power_plugged if battery else None,
        network_interfaces=interfaces,
    )


def metrics_to_dict(m: HardwareMetrics) -> dict:
    return {
        "timestamp": m.timestamp,
        "hostname": m.hostname,
        "platform": m.platform,
        "cpu": {"percent": m.cpu_percent, "cores": m.cpu_count, "freq_mhz": m.cpu_freq_mhz},
        "memory": {"percent": m.memory_percent, "used_gb": m.memory_used_gb, "total_gb": m.memory_total_gb},
        "disk": {"percent": m.disk_percent, "used_gb": m.disk_used_gb, "total_gb": m.disk_total_gb, "free_gb": m.disk_free_gb},
        "battery": {"percent": m.battery_percent, "plugged": m.battery_plugged},
        "network": m.network_interfaces,
        "flags": m.flags,
    }
