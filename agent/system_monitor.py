"""
Module for monitoring system resources.
"""
import platform
import psutil

def get_system_info() -> str:
    """
    Get system information.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime_seconds = (
        psutil.boot_time()
    )

    info = (
        f"""💻 *System Info*
"""
        f"""OS: {platform.system()} {platform.release()}
"""
        f"""CPU: {cpu_percent}%
"""
        f"""RAM: {ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB ({ram.percent}%)
"""
        f"""Disk: {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)
"""
        f"""Python: {platform.python_version()}"""
    )
    return info
