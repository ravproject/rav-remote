import os
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS


def generate_daily_report(period: str = "today") -> str:
    now = datetime.now()
    if period == "yesterday":
        start = now - timedelta(days=1)
        start = start.replace(hour=0, minute=0, second=0)
        end = now.replace(hour=0, minute=0, second=0)
        label = "Kemarin"
    else:
        start = now.replace(hour=0, minute=0, second=0)
        end = now
        label = "Hari Ini"

    lines = [f"Laporan Aktivitas {label} ({start.strftime('%d/%m/%Y')})"]
    lines.append("")

    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/") if not IS_WINDOWS else psutil.disk_usage("C:\\")
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime = now - boot

    lines.append(f"CPU: {cpu}% | RAM: {ram.percent}% | Disk: {disk.percent}%")
    lines.append(f"Uptime: {uptime.days}h {uptime.seconds // 3600}j {uptime.seconds % 3600 // 60}m")
    lines.append(f"Boot: {boot.strftime('%H:%M')}")
    lines.append("")

    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
    lines.append("Top Proses (CPU):")
    for p in procs[:8]:
        lines.append(f"  {p['name']} - CPU: {p.get('cpu_percent', 0):.1f}% Mem: {p.get('memory_percent', 0):.1f}%")

    return "\n".join(lines)
