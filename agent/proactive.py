"""
Proactive Awareness Engine — memberikan notifikasi inisiatif ke user.
"""
import asyncio
import psutil
from loguru import logger
from agent.memory.mcp_collector import mcp_collector

# Shared list for proactive alerts (consumed by heartbeat endpoint)
proactive_alerts: list[str] = []


class ProactiveEngine:
    def __init__(self):
        self.active = False
        self._task = None
        self.check_interval = 300

    async def start(self):
        if self.active:
            return
        self.active = True
        self._task = asyncio.create_task(self._proactive_loop())
        logger.info("🟢 Proactive Engine started")

    async def stop(self):
        self.active = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("🔴 Proactive Engine stopped")

    async def _proactive_loop(self):
        while self.active:
            try:
                alert = await self._check_context()
                if alert:
                    proactive_alerts.append(alert)
            except Exception as e:
                logger.debug(f"Proactive check error: {e}")
            await asyncio.sleep(self.check_interval)

    async def _check_context(self) -> str | None:
        alerts = []

        try:
            from agent.active_window import get_active_window
            win = get_active_window()
            if win and any(kw in win.lower() for kw in ["report", "laporan", "dokumen", "paper", "skripsi", "tugas"]):
                alerts.append(f"📝 Detected working on: `{win}`, need help summarizing?")
        except Exception:
            pass

        try:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            if cpu > 85 or ram > 90:
                alerts.append(f"⚠️ High load (CPU={cpu}%, RAM={ram}%). Run `!process list`?")
        except Exception:
            pass

        try:
            if psutil.cpu_percent(interval=0.1) < 5 and not mcp_collector.active:
                alerts.append("💡 Seems idle. Activate `!mcp on` for context monitoring?")
        except Exception:
            pass

        return alerts[0] if alerts else None


proactive_engine = ProactiveEngine()
