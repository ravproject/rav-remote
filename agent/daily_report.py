"""
Daily Report — summarizes laptop activity for the last 24 hours.
"""
import os
import platform
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

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
    disk = psutil.disk_usage("/")
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

    if platform.system() == "Linux":
        try:
            import subprocess
            res = subprocess.run(["who", "-b"], capture_output=True, text=True, timeout=3)
            if res.stdout:
                lines.append(f"\nSession: {res.stdout.strip()}")
        except Exception:
            pass

    return "\n".join(lines)
