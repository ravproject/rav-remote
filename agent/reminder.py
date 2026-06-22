"""
Reminder System — desktop + Telegram notification scheduler.
"""
import asyncio
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

REMINDER_FILE = Path.home() / ".config" / "rav-remote" / "reminders.json"

class ReminderManager:
    def __init__(self):
        self.reminders = self._load()

    def _load(self) -> list:
        if REMINDER_FILE.exists():
            try:
                with open(REMINDER_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        REMINDER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REMINDER_FILE, "w") as f:
            json.dump(self.reminders, f, indent=2)

    def add(self, text: str, time_str: str) -> str:
        now = datetime.now()
        target = None
        try:
            time_str = time_str.lower().strip()
            if "jam" in time_str:
                hours = int(time_str.replace("jam", "").strip())
                target = now + timedelta(hours=hours)
            elif "h" in time_str:
                hours = int(time_str.replace("h", "").strip())
                target = now + timedelta(hours=hours)
            elif "menit" in time_str:
                minutes = int(time_str.replace("menit", "").strip())
                target = now + timedelta(minutes=minutes)
            elif "m" in time_str:
                minutes = int(time_str.replace("m", "").strip())
                target = now + timedelta(minutes=minutes)
            elif ":" in time_str:
                parts = time_str.split(":")
                target = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0)
                if target < now:
                    target += timedelta(days=1)
        except Exception as e:
            return f"Format waktu tidak dikenal: {e}. Gunakan: '30m', '2jam', '14:30'"
        if not target:
            return "Format waktu tidak dikenal. Gunakan: '30m', '2jam', '14:30'"
        self.reminders.append({"text": text, "time": target.isoformat(), "done": False})
        self._save()
        return f"Pengingat: '{text}' pada {target.strftime('%H:%M %d/%m/%Y')}"

    def list_reminders(self) -> str:
        if not self.reminders:
            return "Tidak ada pengingat."
        lines = ["Daftar Pengingat:"]
        now = datetime.now()
        for i, r in enumerate(self.reminders, 1):
            status = "DONE" if r.get("done") else "PENDING"
            try:
                t = datetime.fromisoformat(r["time"])
                if not r.get("done") and now > t:
                    status = "LEWAT"
                lines.append(f"  {i}. [{status}] {r['text']} ({t.strftime('%H:%M %d/%m')})")
            except Exception:
                lines.append(f"  {i}. [{status}] {r['text']}")
        return "\n".join(lines)

    def delete(self, index: int) -> str:
        if 0 < index <= len(self.reminders):
            removed = self.reminders.pop(index - 1)
            self._save()
            return f"Pengingat '{removed['text']}' dihapus."
        return "Nomor tidak valid."

    async def check_loop(self, notify_func):
        while True:
            now = datetime.now()
            triggered = []
            for r in self.reminders:
                if not r.get("done"):
                    try:
                        t = datetime.fromisoformat(r["time"])
                        if now >= t:
                            r["done"] = True
                            triggered.append(r["text"])
                    except Exception:
                        pass
            if triggered:
                self._save()
                for text in triggered:
                    await notify_func(text)
                    try:
                        subprocess.run(["notify-send", "RAV-REMOTE Reminder", text], timeout=3)
                    except Exception:
                        pass
            await asyncio.sleep(30)

reminder_manager = ReminderManager()
