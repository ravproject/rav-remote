"""
Workspace Manager — save/restore desktop state (open windows, apps, dirs).
"""
import json
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from loguru import logger

WORKSPACE_DIR = Path.home() / ".config" / "rav-remote" / "workspaces"

class WorkspaceManager:
    def __init__(self):
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    def _capture_windows(self) -> list:
        windows = []
        if shutil.which("wmctrl"):
            try:
                res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=5)
                for line in res.stdout.strip().split("\n"):
                    if line:
                        windows.append(line)
            except Exception:
                pass
        return windows

    def _restore_windows(self, windows: list):
        if not windows or not shutil.which("wmctrl"):
            return
        for entry in windows:
            parts = entry.split(None, 3)
            if len(parts) >= 4:
                cmd = parts[3] if parts[3].startswith("/") else parts[3].lower()
                try:
                    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

    def save(self, name: str) -> str:
        state = {
            "timestamp": datetime.now().isoformat(),
            "windows": self._capture_windows(),
            "cwd": os.getcwd()
        }
        filepath = WORKSPACE_DIR / f"{name}.json"
        with open(filepath, "w") as f:
            json.dump(state, f, indent=2)
        return f"Workspace '{name}' tersimpan ({len(state['windows'])} window terdeteksi)."

    def load(self, name: str) -> str:
        filepath = WORKSPACE_DIR / f"{name}.json"
        if not filepath.exists():
            return f"Workspace '{name}' tidak ditemukan."
        try:
            with open(filepath) as f:
                state = json.load(f)
            self._restore_windows(state.get("windows", []))
            return f"Workspace '{name}' dimuat ({len(state.get('windows', []))} window dipulihkan)."
        except Exception as e:
            return f"Gagal memuat workspace '{name}': {e}"

    def list_workspaces(self) -> str:
        files = sorted(WORKSPACE_DIR.glob("*.json"))
        if not files:
            return "Belum ada workspace tersimpan."
        lines = ["Daftar Workspace:"]
        for f in files:
            try:
                with open(f) as fh:
                    data = json.load(fh)
                ts = data.get("timestamp", "unknown")[:16]
                lines.append(f"  {f.stem} ({ts})")
            except Exception:
                lines.append(f"  {f.stem}")
        return "\n".join(lines)

    def delete(self, name: str) -> str:
        filepath = WORKSPACE_DIR / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            return f"Workspace '{name}' dihapus."
        return f"Workspace '{name}' tidak ditemukan."

workspace_manager = WorkspaceManager()
