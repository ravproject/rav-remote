import subprocess
import shutil

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool


def vpn_status() -> str:
    if IS_LINUX and has_tool("nmcli"):
        try:
            r = subprocess.run(["nmcli", "-t", "-f", "TYPE,NAME,DEVICE", "connection", "show", "--active"],
                               capture_output=True, text=True, timeout=5)
            vpns = [l.split(":")[1] for l in r.stdout.splitlines() if l.startswith("vpn:")]
            return f"VPN aktif: {', '.join(vpns)}" if vpns else "Tidak ada VPN aktif."
        except Exception as e:
            return f"Gagal cek VPN: {e}"
    elif IS_MACOS:
        try:
            r = subprocess.run(["scutil", "--nc", "list"], capture_output=True, text=True, timeout=5)
            return f"VPN Services:\n{r.stdout[:500]}"
        except Exception as e:
            return f"Gagal: {e}"
    elif IS_WINDOWS:
        try:
            r = subprocess.run(["powershell", "-Command",
                               "Get-VpnConnection | Select-Object Name,ServerAddress,ConnectionStatus | Format-List"],
                               capture_output=True, text=True, timeout=10)
            return r.stdout[:500] if r.stdout.strip() else "Tidak ada VPN terdeteksi."
        except Exception as e:
            return f"Gagal: {e}"
    return "Fitur VPN belum didukung di OS ini."


def vpn_connect(name: str) -> str:
    if IS_LINUX and has_tool("nmcli"):
        try:
            subprocess.run(["nmcli", "connection", "up", name], capture_output=True, timeout=15)
            return f"VPN '{name}' terhubung."
        except subprocess.TimeoutExpired:
            return f"Timeout koneksi VPN '{name}'."
        except Exception as e:
            return f"Gagal: {e}"
    elif IS_MACOS:
        try:
            subprocess.run(["scutil", "--nc", "start", name], capture_output=True, timeout=15)
            return f"VPN '{name}' terhubung."
        except Exception as e:
            return f"Gagal: {e}"
    elif IS_WINDOWS:
        try:
            r = subprocess.run(["rasdial", name], capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                return f"VPN '{name}' terhubung."
            return f"Gagal: {r.stderr[:200]}"
        except Exception as e:
            return f"Gagal: {e}"
    return "Fitur VPN belum didukung."


def vpn_disconnect(name: str = None) -> str:
    if IS_LINUX and has_tool("nmcli"):
        try:
            if name:
                subprocess.run(["nmcli", "connection", "down", name], capture_output=True, timeout=10)
                return f"VPN '{name}' diputus."
            subprocess.run(["nmcli", "connection", "down"] +
                           [l.split(":")[1] for l in subprocess.run(
                               ["nmcli", "-t", "-f", "TYPE,NAME", "connection", "show", "--active"],
                               capture_output=True, text=True, timeout=5).stdout.splitlines()
                            if l.startswith("vpn:")], capture_output=True, timeout=10)
            return "Semua VPN diputus."
        except Exception as e:
            return f"Gagal: {e}"
    elif IS_MACOS:
        try:
            subprocess.run(["scutil", "--nc", "stop", name or "all"], capture_output=True, timeout=10)
            return "VPN diputus."
        except Exception as e:
            return f"Gagal: {e}"
    elif IS_WINDOWS:
        try:
            subprocess.run(["rasdial", name or "", "/disconnect"], capture_output=True, timeout=10)
            return "VPN diputus."
        except Exception as e:
            return f"Gagal: {e}"
    return "Fitur VPN belum didukung."
