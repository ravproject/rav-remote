import subprocess
import shutil

def vpn_status() -> str:
    if shutil.which("nmcli"):
        try:
            r = subprocess.run(["nmcli", "-t", "-f", "TYPE,NAME,DEVICE", "connection", "show", "--active"],
                              capture_output=True, text=True, timeout=5)
            vpns = [l.split(":")[1] for l in r.stdout.splitlines() if l.startswith("vpn:")]
            if vpns:
                return f"🔒 VPN aktif: {', '.join(vpns)}"
            return "🔓 Tidak ada VPN aktif."
        except Exception as e:
            return f"Gagal cek VPN: {e}"
    return "nmcli tidak ditemukan. Install network-manager."

def vpn_connect(name: str) -> str:
    if not shutil.which("nmcli"):
        return "nmcli tidak ditemukan."
    try:
        subprocess.run(["nmcli", "connection", "up", name], capture_output=True, timeout=15)
        return f"🔒 VPN '{name}' terhubung."
    except subprocess.TimeoutExpired:
        return f"⏱ Timeout koneksi VPN '{name}'."
    except Exception as e:
        return f"Gagal konek VPN: {e}"

def vpn_disconnect(name: str = None) -> str:
    if not shutil.which("nmcli"):
        return "nmcli tidak ditemukan."
    try:
        if name:
            subprocess.run(["nmcli", "connection", "down", name], capture_output=True, timeout=10)
            return f"🔓 VPN '{name}' terputus."
        r = subprocess.run(["nmcli", "-t", "-f", "TYPE,NAME", "connection", "show", "--active"],
                          capture_output=True, text=True, timeout=5)
        vpns = [l.split(":")[1] for l in r.stdout.splitlines() if l.startswith("vpn:")]
        if not vpns:
            return "Tidak ada VPN aktif."
        for v in vpns:
            subprocess.run(["nmcli", "connection", "down", v], capture_output=True, timeout=10)
        return f"🔓 Semua VPN terputus ({len(vpns)})."
    except Exception as e:
        return f"Gagal putus VPN: {e}"
