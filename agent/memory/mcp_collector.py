"""
Memory Context Provider (MCP) — Background collector.
Menyimpan snapshot aktivitas user secara realtime ke MemoryStore.
"""
import os
import asyncio
import platform
from datetime import datetime, timezone
from loguru import logger
from agent.memory.manager import memory_manager


class MCPCollector:
    def __init__(self):
        self.active = False
        self._task = None
        self.interval = 30

    async def start(self):
        if self.active:
            return
        self.active = True
        self._task = asyncio.create_task(self._collect_loop())
        logger.info("🟢 MCP Collector started (interval={}s)", self.interval)

    async def stop(self):
        self.active = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("🔴 MCP Collector stopped")

    async def _collect_loop(self):
        while self.active:
            try:
                await self._collect_snapshot()
            except Exception as e:
                logger.debug(f"MCP collect error: {e}")
            await asyncio.sleep(self.interval)

    async def _collect_snapshot(self):
        context_parts = []

        try:
            from agent.active_window import get_active_window
            win = get_active_window()
            if win:
                context_parts.append(f"Aktif: {win}")
        except Exception:
            pass

        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            load = round(psutil.getloadavg()[0], 1) if hasattr(psutil, "getloadavg") else 0
            if cpu > 80 or ram > 85:
                context_parts.append(f"⚠️ Beban tinggi: CPU={cpu}% RAM={ram}%")
            else:
                context_parts.append(f"Sistem: CPU={cpu}% RAM={ram}% Disk={disk}% Load={load}")
        except Exception:
            pass

        try:
            from agent.smart_clipboard import get_recent_clip
            clip = get_recent_clip()
            if clip:
                context_parts.append(f"Klip: {clip[:200]}")
        except Exception:
            pass

        try:
            from agent.recent_files import get_recent_files
            recent = get_recent_files(minutes=2)
            if recent:
                names = ", ".join(f.name for f in recent[:5])
                context_parts.append(f"File: {names}")
        except Exception:
            pass

        try:
            import psutil
            proc_names = []
            for p in psutil.process_iter(["name", "cwd", "cmdline"]):
                try:
                    name = (p.info["name"] or "").lower()
                    if "code" in name or "cursor" in name:
                        cwd = p.info.get("cwd") or ""
                        if cwd:
                            project = os.path.basename(cwd)
                            proc_names.append(f"VS Code: {project}")
                    elif "gnome-terminal" in name or "ptyxis" in name or "konsole" in name:
                        cwd = p.info.get("cwd") or ""
                        if cwd:
                            project = os.path.basename(cwd)
                            proc_names.append(f"Terminal: {project}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                if len(proc_names) >= 3:
                    break
            if proc_names:
                context_parts.extend(proc_names)
        except Exception:
            pass

        if context_parts:
            text = " | ".join(context_parts)

            # Extract topic dari active window untuk tagging yang lebih relevan
            topic = "aktivitas"
            if win:
                win_lower = win.lower()
                if any(k in win_lower for k in ["kode", "code", "cursor", "ide", "vscode", "pycharm", "intellij"]):
                    topic = "coding"
                elif any(k in win_lower for k in ["figma", "design", "ui", "ux", "canva", "photoshop"]):
                    topic = "desain"
                elif any(k in win_lower for k in ["browser", "chrome", "firefox", "web", "docs"]):
                    topic = "browsing"
                elif any(k in win_lower for k in ["terminal", "bash", "console"]):
                    topic = "terminal"

            try:
                memory_manager.remember(
                    text=text,
                    source="mcp",
                    topic=topic,
                    tags=["auto", "mcp", topic],
                )
            except Exception as e:
                logger.debug(f"MCP store error: {e}")

    def get_recent_context(self, minutes: int = 10) -> str:
        try:
            results = memory_manager.search(
                query="context_snapshot recent activity",
                k=10,
            )
            mcp_results = [r for r in results if r["metadata"].get("topic") == "context_snapshot"]
            if not mcp_results:
                return "No recent context available."
            lines = ["📋 *Recent Context:*"]
            for r in mcp_results[:8]:
                ts = r["metadata"].get("timestamp", "")[11:19]
                lines.append(f"[{ts}] {r['text'][:150]}")
            return "\n".join(lines)
        except Exception:
            return "Context unavailable."


mcp_collector = MCPCollector()
