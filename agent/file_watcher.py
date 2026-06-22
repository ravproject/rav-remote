"""
File Watcher — monitor folder changes and send notifications.
"""
import os
import time
import threading
from pathlib import Path
from datetime import datetime
from loguru import logger

class FileWatcher:
    def __init__(self):
        self.watches = {}
        self._threads = {}

    def start(self, folder: str) -> str:
        target = Path(folder).expanduser()
        if not target.exists():
            return f"❌ Folder tidak ditemukan: {folder}"
        if str(target) in self.watches:
            return f"📡 Sudah memantau: {target}"
        self.watches[str(target)] = {"running": True, "changes": []}
        t = threading.Thread(target=self._watch_loop, args=(target,), daemon=True)
        self._threads[str(target)] = t
        t.start()
        return f"📡 File Watcher AKTIF untuk: {target}"

    def stop(self, folder: str) -> str:
        target = str(Path(folder).expanduser())
        if target in self.watches:
            self.watches[target]["running"] = False
            del self.watches[target]
            return f"📡 File Watcher NONAKTIF untuk: {folder}"
        return f"File Watcher tidak aktif untuk: {folder}"

    def _watch_loop(self, target: Path):
        snapshot = {}
        for p in target.rglob("*"):
            if p.is_file():
                snapshot[str(p)] = p.stat().st_mtime
        while self.watches.get(str(target), {}).get("running", False):
            time.sleep(5)
            for p in target.rglob("*"):
                if p.is_file():
                    key = str(p)
                    mtime = p.stat().st_mtime
                    if key not in snapshot:
                        change = f"➕ File baru: {p.relative_to(target)}"
                        self.watches[str(target)]["changes"].append(change)
                    elif snapshot[key] != mtime:
                        change = f"✏️ Dimodifikasi: {p.relative_to(target)}"
                        self.watches[str(target)]["changes"].append(change)
                    snapshot[key] = mtime

    def get_changes(self, folder: str = None) -> str:
        if folder:
            target = str(Path(folder).expanduser())
            if target in self.watches:
                changes = self.watches[target]["changes"][-20:]
                if not changes:
                    return f"Tidak ada perubahan di {folder} (terakhir dipantau)."
                return f"📡 Perubahan terbaru di {folder}:\n" + "\n".join(changes[-10:])
            return f"Tidak memantau: {folder}"
        if not self.watches:
            return "Tidak ada folder yang dipantau."
        lines = ["📡 Status File Watcher:"]
        for folder, data in self.watches.items():
            lines.append(f"  {folder}: {len(data['changes'])} perubahan")
        return "\n".join(lines)

file_watcher = FileWatcher()
