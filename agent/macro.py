"""
Macro Recorder — record, save, and replay keyboard/mouse actions.
"""
import json
import time
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from loguru import logger

MACRO_DIR = Path.home() / ".config" / "rav-remote" / "macros"

class MacroManager:
    def __init__(self):
        MACRO_DIR.mkdir(parents=True, exist_ok=True)
        self.recording = False
        self.current_macro = []
        self.start_time = None

    def record(self, name: str) -> str:
        if self.recording:
            return "Sudah merekam. Stop dulu sebelum record baru."
        self.recording = True
        self.current_macro = []
        self.start_time = time.time()
        return f"🎬 Merekam macro '{name}'... Kirim !macro stop saat selesai."

    def stop(self) -> str:
        if not self.recording:
            return "Tidak ada rekaman aktif."
        self.recording = False
        return f"⏹️ Rekaman dihentikan ({len(self.current_macro)} aksi terekam)."

    def add_action(self, action: dict):
        if self.recording:
            ts = time.time() - (self.start_time or time.time())
            action["timestamp"] = round(ts, 2)
            self.current_macro.append(action)

    def save(self, name: str) -> str:
        if not self.current_macro:
            return "Tidak ada aksi untuk disimpan."
        filepath = MACRO_DIR / f"{name}.json"
        data = {
            "name": name,
            "created": datetime.now().isoformat(),
            "actions": self.current_macro
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return f"💾 Macro '{name}' tersimpan ({len(self.current_macro)} aksi)."

    def play(self, name: str) -> str:
        filepath = MACRO_DIR / f"{name}.json"
        if not filepath.exists():
            return f"Macro '{name}' tidak ditemukan."
        try:
            with open(filepath) as f:
                data = json.load(f)
            actions = data.get("actions", [])
            if not actions:
                return f"Macro '{name}' kosong."
            for action in actions:
                act = action.get("action", "")
                if act == "click" and shutil.which("xdotool"):
                    x, y = action.get("x", 0), action.get("y", 0)
                    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                                   capture_output=True, timeout=3)
                elif act == "type" and shutil.which("xdotool"):
                    text = action.get("text", "")
                    subprocess.run(["xdotool", "type", text], capture_output=True, timeout=3)
                elif act == "key" and shutil.which("xdotool"):
                    key = action.get("key", "")
                    subprocess.run(["xdotool", "key", key], capture_output=True, timeout=3)
                elif act == "sleep":
                    time.sleep(action.get("duration", 0.5))
                time.sleep(action.get("delay", 0.3))
            return f"▶️ Macro '{name}' diputar ({len(actions)} aksi)."
        except Exception as e:
            return f"Gagal memutar macro '{name}': {e}"

    def list_macros(self) -> str:
        files = sorted(MACRO_DIR.glob("*.json"))
        if not files:
            return "Belum ada macro tersimpan."
        lines = ["Daftar Macro:"]
        for f in files:
            try:
                with open(f) as fh:
                    data = json.load(fh)
                count = len(data.get("actions", []))
                created = data.get("created", "")[:16] if data.get("created") else ""
                lines.append(f"  {f.stem} ({count} aksi, {created})")
            except Exception:
                lines.append(f"  {f.stem}")
        return "\n".join(lines)

    def delete(self, name: str) -> str:
        filepath = MACRO_DIR / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            return f"Macro '{name}' dihapus."
        return f"Macro '{name}' tidak ditemukan."

macro_manager = MacroManager()
