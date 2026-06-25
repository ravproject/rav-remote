"""
MemorySync — Cross-device memory synchronization.
Meng-ekspor snapshot memory (encrypted) dan meng-import di device lain.
"""
import os
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
from security.crypto import crypto


class MemorySync:
    def export_snapshot(self) -> bytes:
        """Export all memory as encrypted JSON snapshot."""
        from agent.memory.manager import memory_manager
        store = memory_manager.store
        entries = store.get_all_entries(limit=10000)
        snapshot = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "device_id": os.uname().nodename,
            "entries": [
                {
                    "id": e["id"],
                    "text": e["text"],
                    "metadata": e["metadata"],
                }
                for e in entries
            ],
        }
        raw = json.dumps(snapshot, ensure_ascii=False).encode()
        encrypted = crypto.encrypt(raw)
        logger.info(f"Memory snapshot exported: {len(entries)} entries, {len(encrypted)} bytes encrypted")
        return encrypted

    def import_snapshot(self, encrypted_data: bytes) -> str:
        """Import encrypted memory snapshot."""
        try:
            raw = crypto.decrypt(encrypted_data)
            snapshot = json.loads(raw.decode())
        except Exception as e:
            return f"❌ Gagal decrypt snapshot: {e}"

        from agent.memory.manager import memory_manager
        store = memory_manager.store
        imported = 0
        skipped = 0
        for entry in snapshot.get("entries", []):
            text = entry.get("text", "")
            metadata = entry.get("metadata", {})
            if not text or len(text.strip()) < 10:
                skipped += 1
                continue
            store.add(text, metadata)
            imported += 1

        logger.info(f"Memory snapshot imported: {imported} new, {skipped} skipped")
        return f"✅ Diimport: {imported} entries baru, {skipped} dilewati (dari {snapshot.get('device_id', 'unknown')})"

    def sync_all(self) -> str:
        """Sync memory with all registered devices."""
        from bot.agent_registry import registry
        devices = registry.get_all()
        if not devices:
            return "📡 Tidak ada device terdaftar. Daftarkan dengan `!multi_device register`."
        snapshot = self.export_snapshot()
        results = []
        for device in devices:
            name = device.get("name", "unknown")
            ip = device.get("ip")
            if not ip:
                results.append(f"  • {name}: no IP configured")
                continue
            try:
                import httpx
                resp = httpx.post(
                    f"http://{ip}:{os.environ.get('AGENT_PORT', '8765')}/memory/import",
                    json={"snapshot": snapshot.hex()},
                    headers={"X-API-Key": os.environ.get("AGENT_API_KEY", "")},
                    timeout=30,
                )
                if resp.status_code == 200:
                    results.append(f"  • {name}: ✅ synced")
                else:
                    results.append(f"  • {name}: ❌ {resp.status_code}")
            except Exception as e:
                results.append(f"  • {name}: ❌ {e}")
        return "📡 *Memory Sync Results:*\n" + "\n".join(results)
