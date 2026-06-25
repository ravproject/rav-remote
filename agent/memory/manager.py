"""
MemoryManager — entry point tunggal untuk semua operasi memory.
Menggunakan ChromaDB built-in embedding function.
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger
from .embeddings import EmbeddingService
from .store import MemoryStore


class MemoryManager:
    def __init__(self):
        self.embeddings = EmbeddingService()
        self.store = MemoryStore(self.embeddings.embed)
        self._loaded = False

    def ensure_loaded(self):
        if not self._loaded:
            self.embeddings.load()
            self._loaded = True

    def remember(self, text: str, source: str = "chat", topic: str = None, tags: list = None):
        self.ensure_loaded()
        metadata = {
            "source": source,
            "device_id": os.uname().nodename,
            "feature": "memory",
            "topic": topic or "general",
            "tags": json.dumps(tags or []),
        }
        chunks = self._chunk_text(text)
        for chunk in chunks:
            self.store.add(chunk, metadata)
        logger.info(f"Memory stored: {len(chunks)} chunks, topic={topic}")

    def search(self, query: str, k: int = 5, topic: str = None) -> list[dict]:
        self.ensure_loaded()
        filt = {"topic": topic} if topic else None
        return self.store.search(query, k=k, where_filter=filt)

    def summarize_all(self, topic: str = None) -> str:
        self.ensure_loaded()
        stats = self.store.stats()
        if stats["total_entries"] == 0:
            return "Belum ada memory tersimpan."
        lines = [f"📚 *Memory Summary ({stats['total_entries']} entries):*"]
        for t, count in sorted(stats["topics"].items(), key=lambda x: -x[1]):
            lines.append(f"  • {t}: {count} entries")
        return "\n".join(lines)

    def forget(self, query: str) -> str:
        self.ensure_loaded()
        results = self.store.search(query, k=5)
        deleted = 0
        for r in results:
            if r["distance"] < 0.35:
                self.store.delete(r["id"])
                deleted += 1
        return f"🗑️ {deleted} memory entries dihapus."

    def stats(self) -> dict:
        self.ensure_loaded()
        return self.store.stats()

    def _chunk_text(self, text: str, max_chars: int = 500) -> list[str]:
        words = text.split()
        chunks = []
        current = []
        current_len = 0
        for w in words:
            if current_len + len(w) + 1 > max_chars and current:
                chunks.append(" ".join(current))
                overlap = []
                overlap_len = 0
                for cw in reversed(current):
                    if overlap_len + len(cw) + 1 > 100:
                        break
                    overlap.insert(0, cw)
                    overlap_len += len(cw) + 1
                current = overlap
                current_len = overlap_len
            current.append(w)
            current_len += len(w) + 1
        if current:
            chunks.append(" ".join(current))
        return chunks or [text]


memory_manager = MemoryManager()
