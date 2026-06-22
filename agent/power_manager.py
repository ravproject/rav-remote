"""
Power Manager — switch between power profiles (performance/balanced/saver).
"""
import os
import subprocess
import shutil
from loguru import logger

def set_power_profile(profile: str = "balanced") -> str:
    profile = profile.lower()
    if profile not in ("performance", "balanced", "saver", "powersaver", "power-saver"):
        return "Profil tidak dikenal. Gunakan: performance, balanced, saver"
    if profile == "saver":
        profile = "power-saver"
    if shutil.which("powerprofilesctl"):
        try:
            subprocess.run(["powerprofilesctl", "set", profile], capture_output=True, timeout=5, check=True)
            return f"⚡ Profil daya: {profile}"
        except subprocess.CalledProcessError as e:
            return f"Gagal set profil {profile}: {e.stderr.decode()[:200]}"
        except Exception as e:
            return f"Gagal: {e}"
    try:
        if profile == "performance":
            for p in ["/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"]:
                if os.path.exists(p):
                    subprocess.run(["sh", "-c", f"echo performance | sudo tee {p}"], capture_output=True, timeout=3)
                    return "⚡ Profil daya: performance (via cpufreq)"
        elif profile == "power-saver":
            for p in ["/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"]:
                if os.path.exists(p):
                    subprocess.run(["sh", "-c", f"echo powersave | sudo tee {p}"], capture_output=True, timeout=3)
                    return "⚡ Profil daya: power-saver (via cpufreq)"
    except Exception:
        pass
    return "Fitur power profile membutuhkan powerprofilesctl (GNOME) atau akses cpufreq."
