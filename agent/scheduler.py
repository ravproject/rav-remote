"""
Scheduler — schedule commands to run at specified times or intervals.
"""
import os
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

SCHEDULE_FILE = Path.home() / ".config" / "rav-remote" / "schedules.json"

class Scheduler:
    def __init__(self):
        self.schedules = self._load()

    def _load(self) -> list:
        if SCHEDULE_FILE.exists():
            try:
                with open(SCHEDULE_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(self.schedules, f, indent=2)

    def add(self, command: str, time_str: str) -> str:
        now = datetime.now()
        target = None
        try:
            time_str = time_str.lower().strip()
            if time_str.startswith("in "):
                parts = time_str[3:].strip().split()
                if parts:
                    val = int(parts[0]) if parts[0].isdigit() else 0
                    if "jam" in time_str or "h" in parts[-1]:
                        target = now + timedelta(hours=val)
                    elif "menit" in time_str or "m" in parts[-1]:
                        target = now + timedelta(minutes=val)
                    elif "detik" in time_str or "s" in parts[-1]:
                        target = now + timedelta(seconds=val)
            elif ":" in time_str:
                parts_ = time_str.split(":")
                target = now.replace(hour=int(parts_[0]), minute=int(parts_[1]), second=0)
                if target < now:
                    target += timedelta(days=1)
            elif time_str == "every weekday" or "weekday" in time_str:
                if ":" in time_str:
                    tpart = time_str.split()[-1]
                    parts_t = tpart.split(":")
                    target = now.replace(hour=int(parts_t[0]), minute=int(parts_t[1]), second=0)
                    if target < now:
                        target += timedelta(days=1)
                else:
                    target = now + timedelta(hours=1)
        except Exception as e:
            return f"Format waktu salah: {e}. Contoh: in 30m, in 2jam, 14:30, every weekday 08:00"
        if not target:
            return "Format waktu tidak dikenal. Contoh: in 30m, 14:30, every weekday 08:00"
        entry = {
            "id": len(self.schedules) + 1,
            "command": command,
            "time": target.isoformat(),
            "created": now.isoformat(),
            "done": False,
            "repeat": "weekday" if "weekday" in time_str else None
        }
        self.schedules.append(entry)
        self._save()
        return f"📅 Terjadwal: '{command}' pada {target.strftime('%H:%M %d/%m/%Y')}"

    def list_schedules(self) -> str:
        if not self.schedules:
            return "Belum ada jadwal."
        lines = ["Daftar Jadwal:"]
        now = datetime.now()
        for s in self.schedules:
            status = "DONE" if s.get("done") else "PENDING"
            try:
                t = datetime.fromisoformat(s["time"])
                if not s.get("done") and now > t:
                    status = "LEWAT"
                lines.append(f"  #{s['id']} [{status}] {s['command']} ({t.strftime('%H:%M %d/%m')})")
            except Exception:
                lines.append(f"  #{s['id']} [{status}] {s['command']}")
        return "\n".join(lines)

    def delete(self, schedule_id: int) -> str:
        for i, s in enumerate(self.schedules):
            if s["id"] == schedule_id:
                removed = self.schedules.pop(i)
                self._save()
                return f"Jadwal #{schedule_id} '{removed['command']}' dihapus."
        return f"Jadwal #{schedule_id} tidak ditemukan."

    async def check_loop(self, execute_func):
        while True:
            now = datetime.now()
            triggered = []
            for s in self.schedules:
                if not s.get("done"):
                    try:
                        t = datetime.fromisoformat(s["time"])
                        if now >= t:
                            s["done"] = True
                            triggered.append(s)
                    except Exception:
                        pass
            if triggered:
                self._save()
                for entry in triggered:
                    try:
                        await execute_func(entry["command"])
                        logger.info(f"Scheduled command executed: {entry['command']}")
                    except Exception as e:
                        logger.error(f"Failed to execute scheduled command: {e}")
            await asyncio.sleep(30)

scheduler = Scheduler()
