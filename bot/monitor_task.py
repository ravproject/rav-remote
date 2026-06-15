"""
Monitor Task — Mengelola status Agent dan Alerting.
Mendukung Pull Model (Bot -> Agent) dan transisi state ONLINE/DEGRADED/OFFLINE.
"""
import asyncio
import time
from loguru import logger
from telegram.ext import Application
import os
from html import escape

# State monitoring: {agent_id: {"state": "ONLINE", "last_seen": timestamp}}
_agent_status = {}
_status_lock: asyncio.Lock | None = None

def _get_lock() -> asyncio.Lock:
    global _status_lock
    if _status_lock is None:
        _status_lock = asyncio.Lock()
    return _status_lock

# Thresholds
TIMEOUT_DEGRADED = 90   # 1.5 menit tanpa heartbeat
TIMEOUT_OFFLINE = 180    # 3 menit tanpa heartbeat

class MonitorTask:
    def __init__(self, app: Application):
        self.app = app
        self.allowed_users = set(os.environ.get("ALLOWED_USER_IDS", "").split(","))

    async def update_heartbeat(self, agent_id: str, metrics: dict):
        """Update last seen dan cek transisi state."""
        now = time.time()
        alert_msg = None
        
        async with _get_lock():
            prev_data = _agent_status.get(agent_id, {"state": "OFFLINE", "last_seen": 0})
            prev_state = prev_data["state"]

            _agent_status[agent_id] = {
                "state": "ONLINE",
                "last_seen": now,
                "metrics": metrics
            }

            if prev_state != "ONLINE":
                cpu = escape(str(metrics.get('cpu', '0')))
                ram = escape(str(metrics.get('ram', '0')))
                alert_msg = f"✅ <b>Agent Online:</b> {escape(agent_id)}\nMetrics: CPU {cpu}% | RAM {ram}%"
                logger.info(f"Agent {agent_id} transitioned to ONLINE")
                
        if alert_msg:
            await self._broadcast_alert(alert_msg)

    async def _check_status_once(self, now: float):
        """Satu iterasi pengecekan status (dipisahkan untuk testing)."""
        alerts_to_send = []
        
        async with _get_lock():
            for agent_id, data in list(_agent_status.items()):
                elapsed = now - data["last_seen"]
                current_state = data["state"]

                if elapsed > TIMEOUT_OFFLINE and current_state != "OFFLINE":
                    data["state"] = "OFFLINE"
                    alerts_to_send.append(
                        f"🔴 <b>Agent Offline:</b> {escape(agent_id)}\n"
                        f"Terakhir terlihat {int(elapsed/60)} menit yang lalu."
                    )
                    logger.warning(f"Agent {agent_id} transitioned to OFFLINE")

                elif elapsed > TIMEOUT_DEGRADED and current_state == "ONLINE":
                    data["state"] = "DEGRADED"
                    alerts_to_send.append(
                        f"⚠️ <b>Agent Degraded:</b> {escape(agent_id)}\n"
                        f"Koneksi mungkin fluktuatif."
                    )
                    logger.warning(f"Agent {agent_id} transitioned to DEGRADED")
                    
        for msg in alerts_to_send:
            await self._broadcast_alert(msg)

    async def run_monitoring_loop(self):
        """Background loop untuk mengecek timeout heartbeat."""
        while True:
            await self._check_status_once(time.time())
            await asyncio.sleep(30)

    async def _broadcast_alert(self, message: str):
        """Kirim pesan ke semua user yang terdaftar."""
        for user_id in self.allowed_users:
            try:
                if user_id:
                    await self.app.bot.send_message(chat_id=user_id, text=message, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to broadcast alert to {user_id}: {e}")
