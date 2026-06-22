import psutil
import shutil
import subprocess
from datetime import datetime

def get_dashboard() -> str:
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot
    h, r = divmod(int(uptime.total_seconds()), 3600)
    m, _ = divmod(r, 60)
    processes = len(psutil.pids())
    net = psutil.net_io_counters()
    lines = [
        "📊 **RAV DASHBOARD**",
        f"🖥 CPU: {cpu}%",
        f"💾 RAM: {mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB ({mem.percent}%)",
        f"💿 Disk: {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)",
        f"📡 Proses: {processes}",
        f"⏱ Uptime: {h}j {m}m",
        f"🌐 Network: ↑{net.bytes_sent // (1024**2)}MB ↓{net.bytes_recv // (1024**2)}MB",
        f"🔋 Baterai: {psutil.sensors_battery().percent if psutil.sensors_battery() else 'N/A'}%",
    ]
    return "\n".join(lines)
