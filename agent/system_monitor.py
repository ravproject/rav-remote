"""
System Monitor — Collector untuk metrics dan heartbeat.
Pull Model: Agent menyediakan metrics melalui endpoint /system/heartbeat.
"""
import platform
import psutil
import os
from loguru import logger

class SystemMonitor:
    def __init__(self):
        self.agent_id = os.environ.get("AGENT_ID", platform.node())

    def get_metrics(self) -> dict:
        """Ambil snapshot CPU dan RAM."""
        return {
            "cpu": psutil.cpu_percent(interval=1),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
            "hostname": platform.node()
        }

    def get_system_summary(self) -> str:
        """Rangkuman untuk perintah !sysinfo."""
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return (
            f"💻 *System Info ({self.agent_id})*\n"
            f"OS: {platform.system()} {platform.release()}\n"
            f"CPU: {cpu}%\n"
            f"RAM: {ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB ({ram.percent}%)\n"
            f"Disk: {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)\n"
            f"Python: {platform.python_version()}"
        )

sys_monitor = SystemMonitor()
