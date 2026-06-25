import os
import sys
import shutil
import platform
import subprocess
import importlib.util
import re
from pathlib import Path


SYSTEM = platform.system()
IS_LINUX = SYSTEM == "Linux"
IS_MACOS = SYSTEM == "Darwin"
IS_WINDOWS = SYSTEM == "Windows"


def get_os() -> str:
    return SYSTEM


def get_os_lower() -> str:
    return SYSTEM.lower()


def detect_desktop() -> str:
    if IS_LINUX:
        de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in de or "ubuntu" in de:
            return "gnome"
        if "kde" in de:
            return "kde"
        if "sway" in de or "i3" in de or "hyprland" in de:
            return "wlroots"
        return "other-x11"
    if IS_MACOS:
        return "macos"
    if IS_WINDOWS:
        return "windows"
    return "unknown"


def is_wayland() -> bool:
    if not IS_LINUX:
        return False
    return "WAYLAND_DISPLAY" in os.environ or os.environ.get("XDG_SESSION_TYPE") == "wayland"


def has_tool(name: str) -> bool:
    if IS_WINDOWS:
        result = shutil.which(name)
        if result:
            return True
        ext = os.environ.get("PATHEXT", "").split(os.pathsep)
        for e in ext:
            if shutil.which(name + e.lower()):
                return True
        return False
    return shutil.which(name) is not None


def has_python_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_cmd(cmd, timeout: int = 10, check: bool = False) -> subprocess.CompletedProcess:
    kwargs = {"capture_output": True, "text": True, "timeout": timeout}
    try:
        if isinstance(cmd, str):
            return subprocess.run(cmd, shell=True, **kwargs)
        return subprocess.run(cmd, **kwargs)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 1, "", f"Timeout ({timeout}s)")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def run_bg(cmd):
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if isinstance(cmd, str):
        return subprocess.Popen(cmd, shell=True, **kwargs)
    return subprocess.Popen(cmd, **kwargs)


def find_executables(*names: str) -> dict:
    return {name: shutil.which(name) for name in names}


def open_file_or_url(target: str) -> bool:
    if IS_LINUX:
        cmd = ["xdg-open", target]
    elif IS_MACOS:
        cmd = ["open", target]
    elif IS_WINDOWS:
        cmd = ["start", target]
    else:
        return False
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def get_app_launch_cmd(app_id: str) -> list[str]:
    if IS_LINUX:
        if has_tool("gtk-launch"):
            return ["gtk-launch", app_id]
        return ["sh", "-c", f"{app_id} &"]
    elif IS_MACOS:
        app_name = app_id.replace(".desktop", "").replace("-", " ")
        return ["open", "-a", app_name]
    elif IS_WINDOWS:
        return ["cmd", "/c", "start", "", app_id]
    return [app_id]


def launch_app(app_id_or_path: str) -> str:
    cmd = get_app_launch_cmd(app_id_or_path)
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Meluncurkan {app_id_or_path}"
    except Exception as e:
        return f"Gagal meluncurkan {app_id_or_path}: {e}"


def get_platform_paths() -> dict:
    paths = {"home": str(Path.home())}
    if IS_LINUX:
        paths.update({
            "temp": "/tmp",
            "cache": Path.home() / ".cache",
            "config": Path.home() / ".config",
            "apps_dirs": ["/usr/share/applications", "/usr/local/share/applications",
                          str(Path.home() / ".local/share/applications")],
            "hosts": "/etc/hosts",
            "temp_dir": "/tmp",
        })
    elif IS_MACOS:
        paths.update({
            "temp": Path.home() / "Library/Caches",
            "cache": Path.home() / "Library/Caches",
            "config": Path.home() / "Library/Preferences",
            "apps_dirs": ["/Applications", str(Path.home() / "Applications")],
            "hosts": "/etc/hosts",
            "temp_dir": "/tmp",
        })
    elif IS_WINDOWS:
        paths.update({
            "temp": os.environ.get("TEMP", "C:\\Windows\\Temp"),
            "cache": Path.home() / "AppData/Local",
            "config": Path.home() / "AppData/Roaming",
            "apps_dirs": [os.path.expandvars("%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs"),
                          os.path.expandvars("%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs")],
            "hosts": "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "temp_dir": os.environ.get("TEMP", "C:\\Windows\\Temp"),
        })
    return paths


def get_desktop_apps() -> list[dict]:
    apps = []
    if IS_LINUX:
        for apps_dir in get_platform_paths()["apps_dirs"]:
            d = Path(apps_dir)
            if d.exists():
                for f in d.glob("*.desktop"):
                    try:
                        name = ""
                        exec_cmd = ""
                        icon = ""
                        with open(f) as fh:
                            for line in fh:
                                if line.startswith("Name="):
                                    name = line.split("=", 1)[1].strip()
                                elif line.startswith("Exec="):
                                    exec_cmd = line.split("=", 1)[1].strip()
                                elif line.startswith("Icon="):
                                    icon = line.split("=", 1)[1].strip()
                        if name and exec_cmd:
                            apps.append({
                                "name": name, "id": f.stem,
                                "exec": exec_cmd, "icon": icon
                            })
                    except Exception:
                        pass
    elif IS_MACOS:
        apps_dir = Path("/Applications")
        if apps_dir.exists():
            for app_bundle in apps_dir.glob("*.app"):
                name = app_bundle.stem
                apps.append({"name": name, "id": name, "exec": str(app_bundle), "icon": ""})
    elif IS_WINDOWS:
        for apps_dir in get_platform_paths()["apps_dirs"]:
            d = Path(apps_dir)
            if d.exists():
                for lnk in d.rglob("*.lnk"):
                    name = lnk.stem
                    apps.append({"name": name, "id": name, "exec": str(lnk), "icon": ""})
    return apps
