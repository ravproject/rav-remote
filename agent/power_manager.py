import os
import subprocess
import shutil
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool


def set_power_profile(profile: str = "balanced") -> str:
    profile = profile.lower()
    if profile not in ("performance", "balanced", "saver", "powersaver", "power-saver"):
        return "Profil tidak dikenal. Gunakan: performance, balanced, saver"
    if profile == "saver":
        profile = "power-saver"

    if IS_LINUX:
        if has_tool("powerprofilesctl"):
            try:
                subprocess.run(["powerprofilesctl", "set", profile], capture_output=True, timeout=5, check=True)
                return f"Profil daya: {profile}"
            except subprocess.CalledProcessError as e:
                return f"Gagal: {e.stderr.decode()[:200]}"
            except Exception as e:
                return f"Gagal: {e}"
        try:
            gov = "performance" if profile == "performance" else "powersave"
            p = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
            if os.path.exists(p):
                subprocess.run(["sh", "-c", f"echo {gov} | sudo tee {p}"], capture_output=True, timeout=3)
                return f"Profil daya: {profile} (via cpufreq)"
        except Exception:
            pass
        return "Fitur power profile butuh powerprofilesctl."

    elif IS_MACOS:
        if profile == "performance":
            subprocess.run(["sudo", "pmset", "-a", "settings", "performance"],
                           capture_output=True, timeout=5)
            return "Profil daya: performance"
        else:
            subprocess.run(["sudo", "pmset", "-a", "lowpowermode", "1"],
                           capture_output=True, timeout=5)
            return "Profil daya: power-saver"

    elif IS_WINDOWS:
        guid_map = {
            "performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
            "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
            "power-saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
        }
        guid = guid_map.get(profile, guid_map["balanced"])
        try:
            subprocess.run(["powercfg", "/setactive", guid], capture_output=True, timeout=5)
            return f"Profil daya: {profile}"
        except Exception as e:
            return f"Gagal: {e}"

    return "Power profile belum didukung di OS ini."
