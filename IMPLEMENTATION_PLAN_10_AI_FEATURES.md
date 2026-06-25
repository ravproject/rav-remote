# RAV-REMOTE AI: Implementation Plan — 10 Advanced Intelligence Features

> **Target:** Implement 10 kecerdasan AI canggih secara bertahap  
> **Basis Kode:** RAV-REMOTE v1.0.4 (Python FastAPI + Node.js Baileys)  
> **Dokumen Perencanaan:** 25 Juni 2026

---

## Daftar Isi

1. [Arsitektur Umum & Fondasi](#1-arsitektur-umum--fondasi)
2. [Dependency Graph & Prioritas](#2-dependency-graph--prioritas)
3. [Fase Implementasi](#3-fase-implementasi)
4. [Detail 10 Fitur](#4-detail-10-fitur)
   - [Fitur 1: Long-Term Memory (RAG)](#fitur-1-long-term-memory-rag)
   - [Fitur 2: Self-Feature Generation](#fitur-2-self-feature-generation)
   - [Fitur 3: MCP — Memory Context Provider](#fitur-3-mcp--memory-context-provider)
   - [Fitur 4: Personal Virtual Companion](#fitur-4-personal-virtual-companion)
   - [Fitur 5: Advanced Problem Solver](#fitur-5-advanced-problem-solver)
   - [Fitur 6: Daily Self-Introspection & Auto Evolution](#fitur-6-daily-self-introspection--auto-evolution)
   - [Fitur 7: Personalized Usage Optimization Advisor](#fitur-7-personalized-usage-optimization-advisor)
   - [Fitur 8: Proactive & Reactive Awareness](#fitur-8-proactive--reactive-awareness)
   - [Fitur 9: Continuous Knowledge Enrichment](#fitur-9-continuous-knowledge-enrichment)
   - [Fitur 10: Advanced Autonomous Agent Mode](#fitur-10-advanced-autonomous-agent-mode)
5. [Modifikasi File Existing](#5-modifikasi-file-existing)
6. [File Baru](#6-file-baru)
7. [Daftar Dependensi Baru](#7-daftar-dependensi-baru)
8. [Strategi Testing](#8-strategi-testing)
9. [Risk & Mitigation](#9-risk--mitigation)

---

## 1. Arsitektur Umum & Fondasi

### 1.1 Diagram Komponen Baru

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAV-REMOTE AI Core                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐    ┌──────────────────────────────┐   │
│  │   Memory System       │    │    AI Orchestrator            │   │
│  │   (ChromaDB Vector)   │◄──►│  (Router + Pipeline)         │   │
│  └──────────┬───────────┘    └──────────┬───────────────────┘   │
│             │                           │                        │
│  ┌──────────▼───────────┐    ┌──────────▼───────────────────┐   │
│  │  Embedding Service   │    │  Tool Execution Layer         │   │
│  │  (sentence-transform)│    │  (opencode, agy, NIM, dll)   │   │
│  └──────────────────────┘    └──────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────┐    ┌──────────────────────────────┐   │
│  │  Knowledge Base      │    │  Self-Evolution Engine       │   │
│  │  (web scraping +     │◄──►│  (auto debug, test, fix)    │   │
│  │   enrichment)        │    └──────────────────────────────┘   │
│  └──────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow Umum (Semua Fitur)

```
User: "!memory search 'desain UI kemarin'"
  → CommandRouter.route()
  → MemoryHandler.search("desain UI kemarin")
  → ChromaDB similarity search (384-d vector)
  → Retrieve top-5 chunks + metadata
  → Format response with context
  → Kirim balik ke user
```

### 1.3 Storage Strategy

**Vector Database — ChromaDB (persistent):**
- Lokasi: `~/.config/rav-remote/memory/chroma/`
- Model embedding: `all-MiniLM-L6-v2` (384-d, ~25MB RAM)
- Collection: `rav_memory` untuk semua fitur
- Metadata fields: `timestamp, source, user_id, feature, device_id`

**JSON File Storage (tetap dipertahankan):**
- Memory index: `~/.config/rav-remote/memory/index.json`
- Knowledge base: `~/.config/rav-remote/knowledge/`
- Feature registry: `~/.config/rav-remote/features/registry.json`
- Evolution log: `~/.config/rav-remote/evolution/log.json`

---

## 2. Dependency Graph & Prioritas

```
Fitur 1 (Memory) ───► Fitur 3 (MCP) ───► Fitur 4 (Companion)
      │                                     │
      │                                     ├──► Fitur 7 (Optimizer)
      │                                     │
      │                                     └──► Fitur 8 (Proactive)
      │
      ├──► Fitur 5 (Problem Solver) ◄── Fitur 9 (Knowledge)
      │
      └──► Fitur 2 (Self-Feature) ───► Fitur 6 (Self-Evolution)
                                          │
                                          └──► Fitur 10 (Autonomous Agent)
```

### Prioritas Implementasi

| Prioritas | Fitur | Alasan |
|-----------|-------|--------|
| **P0** | #1 Long-Term Memory | Fondasi semua fitur cerdas |
| **P0** | #3 MCP | Context provider untuk semua fitur |
| **P1** | #4 Companion | Memanfaatkan memory + MCP |
| **P1** | #5 Problem Solver | Web access + memory |
| **P2** | #9 Knowledge Enrichment | Backfill knowledge base |
| **P2** | #2 Self-Feature Gen | Butuh opencode + agy existing |
| **P3** | #8 Proactive | Butuh memory + scheduler |
| **P3** | #7 Optimizer | Butuh usage analytics |
| **P4** | #6 Self-Evolution | Butuh semua fitur sebelumnya |
| **P4** | #10 Autonomous Agent | Puncak integrasi semua fitur |

---

## 3. Fase Implementasi

### Fase 0: Foundation (Minggu 1)

**Target:** Setup infrastruktur dasar yang dipakai semua fitur.

| Task | File | Durasi |
|------|------|--------|
| Install ChromaDB + sentence-transformers | `requirements.txt` | 15m |
| Buat `agent/memory/` package structure | `agent/memory/__init__.py` | 10m |
| Implement `MemoryStore` class | `agent/memory/store.py` | 3h |
| Implement `EmbeddingService` class | `agent/memory/embeddings.py` | 2h |
| Buat `MemoryManager` (orchestrator) | `agent/memory/manager.py` | 2h |
| Unit test memory CRUD + search | `tests/test_memory.py` | 2h |
| Warmup embedding model on startup | `agent/main.py` | 30m |
| Enkripsi sensitive memory chunks | `security/crypto.py` (modify) | 1h |

### Fase 1: Memory + MCP (Minggu 2)

**Target:** #1 Long-Term Memory + #3 MCP aktif.

| Task | File | Durasi |
|------|------|--------|
| `!memory` command handler + router | `agent/command_handler.py` | 3h |
| `!memory` AI prompt templates | `ai_module/prompt_templates.py` | 30m |
| `!mcp` background collector service | `agent/memory/mcp_collector.py` | 4h |
| `!mcp` query handler | `bot/command_router.py` | 2h |
| Cross-device sync (encrypted) | `agent/memory/sync.py` | 3h |
| Config YAML entries | `config/allowed_commands.yaml` | 15m |
| Fallback parser entries | `ai_module/fallback_parser.py` | 10m |

### Fase 2: Companion + Problem Solver (Minggu 3)

**Target:** #4 Companion + #5 Problem Solver siap pakai.

| Task | File | Durasi |
|------|------|--------|
| `!companion` handler with emotional AI | `agent/companion.py` | 4h |
| Companion prompt engineering | `ai_module/prompts/companion.txt` | 2h |
| `!solve` handler with web scraping | `agent/solver.py` | 4h |
| Safe web scraper (rate-limited) | `agent/scraper.py` (modify) | 2h |
| Router entries + audit logging | `bot/command_router.py` | 1h |
| Config YAML entries | `config/allowed_commands.yaml` | 15m |

### Fase 3: Knowledge + Self-Feature (Minggu 4)

**Target:** #9 Knowledge Enrichment + #2 Self-Feature Generation.

| Task | File | Durasi |
|------|------|--------|
| Knowledge base manager | `agent/knowledge.py` | 3h |
| `!learn` handler | `agent/command_handler.py` | 2h |
| `!create feature` handler | `agent/self_feature.py` | 5h |
| Safe code generation guard | `agent/self_feature.py` | 3h |
| Backup system before code mods | `agent/self_feature.py` | 1h |
| Router entries | `bot/command_router.py` | 1h |

### Fase 4: Proactive + Optimizer (Minggu 5)

**Target:** #8 Proactive + #7 Usage Optimizer.

| Task | File | Durasi |
|------|------|--------|
| Usage analytics collector | `agent/analytics.py` | 3h |
| `!optimize me` handler | `agent/optimizer.py` | 3h |
| Proactive engine (background) | `agent/proactive.py` | 4h |
| Proactive trigger scheduler | `agent/scheduler.py` (modify) | 1h |
| Router entries | `bot/command_router.py` | 30m |

### Fase 5: Self-Evolution + Autonomous Agent (Minggu 6)

**Target:** #6 Self-Evolution + #10 Autonomous Agent.

| Task | File | Durasi |
|------|------|--------|
| `!self evolve` engine | `agent/evolution.py` | 5h |
| Auto bug detection + fix | `agent/evolution.py` | 3h |
| Evolution report generator | `agent/evolution.py` | 2h |
| `!agent` mode orchestrator | `agent/autonomous_agent.py` | 6h |
| Sub-goal planner | `agent/autonomous_agent.py` | 3h |
| Router entries | `bot/command_router.py` | 30m |
| Integration testing | `tests/test_evolution.py` | 3h |

---

## 4. Detail 10 Fitur

---

### Fitur 1: Long-Term Memory (RAG)

> **Command:** `!memory [search|summarize|forget|stats|sync]`  
> **File Baru:** `agent/memory/store.py`, `agent/memory/embeddings.py`, `agent/memory/manager.py`, `agent/memory/sync.py`

#### Arsitektur

```
MemoryManager
 ├── MemoryStore (ChromaDB CRUD)
 │    ├── add(chunks: list[str], metadata: dict)
 │    ├── search(query: str, k: int = 5) -> list[ChunkResult]
 │    ├── delete(filter: dict)
 │    └── stats() -> dict
 ├── EmbeddingService (sentence-transformers)
 │    └── embed(text: str) -> list[float]
 └── MemorySync
      ├── export_snapshot() -> bytes (encrypted)
      └── import_snapshot(data: bytes)
```

#### Skema Collection ChromaDB

```python
collection = {
    "name": "rav_memory",
    "metadata": {
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 100,
        "hnsw:M": 16,
    }
}
# Document schema:
# - id: sha256(chunk_text[:50] + timestamp)
# - embedding: float[384]
# - metadata: {
#     "timestamp": ISO8601,
#     "source": "chat|command|file|mcp|learn",
#     "user_id": hash,
#     "device_id": str,
#     "feature": "memory|companion|solver|mcp",
#     "topic": str | null,
#     "tags": list[str] | null,
#   }
```

#### Implementasi Detail

**`agent/memory/embeddings.py`:**

```python
"""
Embedding Service — mengubah teks ke vector 384-d.
Menggunakan sentence-transformers all-MiniLM-L6-v2.
"""
import numpy as np
from loguru import logger

class EmbeddingService:
    def __init__(self):
        self.model = None
        self.dimension = 384

    def load(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded (384-d)")

    def embed(self, text: str) -> list[float]:
        if self.model is None:
            self.load()
        vec = self.model.encode(text[:2048], normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.model is None:
            self.load()
        vecs = self.model.encode(
            [t[:2048] for t in texts],
            normalize_embeddings=True
        )
        return [v.tolist() for v in vecs]
```

**`agent/memory/store.py`:**

```python
"""
MemoryStore — ChromaDB persistent vector store.
Lokasi: ~/.config/rav-remote/memory/chroma/
"""
import os
import json
import hashlib
import chromadb
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from loguru import logger

CHROMA_DIR = Path.home() / ".config" / "rav-remote" / "memory" / "chroma"
INDEX_FILE = CHROMA_DIR.parent / "index.json"

class MemoryStore:
    def __init__(self, embedding_fn):
        self.embedding_fn = embedding_fn
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(str(CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(
            name="rav_memory",
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 100,
                "hnsw:M": 16,
            },
            embedding_function=None  # We provide embeddings manually
        )
        self._load_index()

    def _load_index(self):
        if INDEX_FILE.exists():
            with open(INDEX_FILE) as f:
                self.index = json.load(f)
        else:
            self.index = {"entries": 0, "topics": {}}

    def _save_index(self):
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INDEX_FILE, "w") as f:
            json.dump(self.index, f)

    def _make_id(self, text: str) -> str:
        raw = f"{text[:50]}{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def add(self, text: str, metadata: dict):
        if not text or len(text.strip()) < 10:
            return
        doc_id = self._make_id(text)
        embedding = self.embedding_fn(text)
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text.strip()[:2048]],
            metadatas=[{
                **metadata,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }]
        )
        self.index["entries"] += 1
        topic = metadata.get("topic", "general")
        self.index["topics"][topic] = self.index["topics"].get(topic, 0) + 1
        self._save_index()

    def search(self, query: str, k: int = 5, filter: Optional[dict] = None) -> list[dict]:
        emb = self.embedding_fn(query)
        kwargs = {
            "query_embeddings": [emb],
            "n_results": k,
        }
        if filter:
            kwargs["where"] = filter
        results = self.collection.query(**kwargs)
        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results["distances"] else 0,
            })
        return output

    def delete(self, doc_id: str):
        self.collection.delete(ids=[doc_id])
        self.index["entries"] = max(0, self.index["entries"] - 1)
        self._save_index()

    def stats(self) -> dict:
        return {
            "total_entries": self.index["entries"],
            "topics": self.index["topics"],
            "chroma_count": self.collection.count(),
        }
```

**`agent/memory/manager.py`** — Orchestrator:

```python
"""
MemoryManager — entry point tunggal untuk semua operasi memory.
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
        # Chunk long texts
        chunks = self._chunk_text(text)
        for chunk in chunks:
            self.store.add(chunk, metadata)
        logger.info(f"Memory stored: {len(chunks)} chunks, topic={topic}")

    def search(self, query: str, k: int = 5, topic: str = None) -> list[dict]:
        self.ensure_loaded()
        filt = {"topic": topic} if topic else None
        results = self.store.search(query, k=k, filter=filt)
        return results

    def summarize_all(self, topic: str = None) -> str:
        self.ensure_loaded()
        stats = self.store.stats()
        if stats["total_entries"] == 0:
            return "Belum ada memory tersimpan."
        lines = [f"📚 Memory Summary ({stats['total_entries']} entries):"]
        for t, count in sorted(stats["topics"].items(), key=lambda x: -x[1]):
            lines.append(f"  • {t}: {count} entries")
        return "\n".join(lines)

    def forget(self, query: str):
        self.ensure_loaded()
        results = self.store.search(query, k=3)
        deleted = 0
        for r in results:
            if r["distance"] < 0.3:
                self.store.delete(r["id"])
                deleted += 1
        return f"🗑️ {deleted} memory entries dihapus."

    def _chunk_text(self, text: str, max_chars: int = 500) -> list[str]:
        """Split text into overlapping chunks for better retrieval."""
        words = text.split()
        chunks = []
        current = []
        current_len = 0
        for w in words:
            if current_len + len(w) + 1 > max_chars and current:
                chunks.append(" ".join(current))
                # overlap: keep last ~100 chars
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

# Module-level singleton
memory_manager = MemoryManager()
```

#### `!memory` Handler di `agent/command_handler.py`:

```python
async def handle_memory(self, args: list[str]) -> str:
    from agent.memory.manager import memory_manager
    if not args:
        return (
            "📝 *Memory System*\n"
            "`!memory search <query>` — Cari memory\n"
            "`!memory summarize [topic]` — Ringkasan semua memory\n"
            "`!memory forget <query>` — Hapus memory terkait\n"
            "`!memory stats` — Statistik memory\n"
            "`!memory sync` — Sinkron antar device"
        )
    sub = args[0].lower()
    if sub == "search":
        query = " ".join(args[1:])
        if not query:
            return "❌ Masukkan query pencarian."
        results = memory_manager.search(query)
        if not results:
            return "🔍 Tidak ada hasil yang relevan."
        lines = ["🔍 *Memory Search Results:*\n"]
        for r in results[:5]:
            score = f"{(1 - r['distance']) * 100:.0f}%" if r["distance"] else "N/A"
            lines.append(f"📌 `[{score}]` {r['text'][:200]}")
        return "\n".join(lines)
    elif sub == "summarize":
        topic = " ".join(args[1:]) or None
        return memory_manager.summarize_all(topic)
    elif sub == "forget":
        query = " ".join(args[1:])
        return memory_manager.forget(query)
    elif sub == "stats":
        stats = memory_manager.store.stats()
        return (
            f"📊 *Memory Stats*\n"
            f"Total entries: {stats['total_entries']}\n"
            f"Topics: {', '.join(f'{t}({c})' for t, c in stats['topics'].items())}"
        )
    elif sub == "sync":
        from agent.memory.sync import MemorySync
        sync = MemorySync()
        return sync.sync_all()
    return "❌ Subperintah tidak dikenal."
```

#### Modifikasi `agent/main.py` — Startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Laptop Agent starting...")
    check_system_dependencies()

    # Warmup embedding model in background
    try:
        from agent.memory.manager import memory_manager
        asyncio.create_task(_warmup_memory())
    except Exception as e:
        logger.warning(f"Memory system init: {e}")

    # existing code...

async def _warmup_memory():
    from agent.memory.manager import memory_manager
    memory_manager.ensure_loaded()
    logger.info("✅ Memory system ready (384-d embeddings)")
```

---

### Fitur 2: Self-Feature Generation & Safe Auto Development

> **Command:** `!create feature <deskripsi>`  
> **File Baru:** `agent/self_feature.py`, `agent/safe_backup.py`

#### Alur Kerja

```
1. User: "!create feature auto-summarize zoom meeting"
2. Validasi: apakah fitur sudah ada? check existing commands
3. Konfirmasi: "Saya akan buat fitur baru. Lanjutkan? (yes/no)"
4. Backup: snapshot semua file yang akan diubah
5. Generate: AI NIM generate kode (handler + router + yaml)
6. Test: jalankan syntax check + import test
7. Install: inject ke command_handler.py + router + yaml
8. Report: "✅ Fitur auto-summarize terinstal. File: ..."
```

#### Implementasi `agent/self_feature.py`:

```python
"""
Self-Feature Generation & Safe Auto Development.
Memanfaatkan NIM AI + opencode untuk generate fitur baru.
"""
import os
import json
import asyncio
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from loguru import logger
from ai_module.nim_client import NIMClient

FEATURES_DIR = Path.home() / ".config" / "rav-remote" / "features"
BACKUP_DIR = Path.home() / ".config" / "rav-remote" / "backups"
FEATURES_REGISTRY = FEATURES_DIR / "registry.json"

FEATURE_GEN_PROMPT = """You are an expert Python developer for RAV-REMOTE (remote laptop control via Telegram/WhatsApp).
Generate a complete new feature implementation based on the user's request.

The system architecture is:
- Handler method in agent/command_handler.py (add new method handle_{feature_name})
- Route entry in bot/command_router.py (elif command_name == "{feature_name}":)
- Whitelist entry in config/allowed_commands.yaml
- Alias in ai_module/fallback_parser.py COMMAND_MAP
- AI prompt update in ai_module/prompt_templates.py

You must respond with ONLY a JSON object containing:
```json
{{
  "feature_name": "snake_case_name",
  "handler_code": "complete Python method code for agent/command_handler.py",
  "router_code": "the elif block for bot/command_router.py",
  "yaml_entry": "YAML entry for config/allowed_commands.yaml",
  "fallback_entry": "COMMAND_MAP entry line",
  "description": "Short description",
  "dependencies": ["list", "of", "pip", "packages"] or []
}}
```

RULES:
- Handler must follow existing patterns (async, self.auditor.log_event, InputSanitizer)
- Must be safe: no destructive commands, no shell injection
- Use existing utilities (self.sanitizer, self.auditor, etc.)
- Max 200 lines of code per feature
"""

class SelfFeatureEngine:
    def __init__(self):
        self.nim = NIMClient()
        FEATURES_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self._load_registry()

    def _load_registry(self):
        if FEATURES_REGISTRY.exists():
            with open(FEATURES_REGISTRY) as f:
                self.registry = json.load(f)
        else:
            self.registry = {"features": [], "generated_count": 0}

    def _save_registry(self):
        FEATURES_DIR.mkdir(parents=True, exist_ok=True)
        with open(FEATURES_REGISTRY, "w") as f:
            json.dump(self.registry, f, indent=2)

    async def generate_feature(self, description: str) -> dict:
        """Generate complete feature code from description."""
        # Check existing commands first
        from ai_module.fallback_parser import FallbackParser
        existing = set(FallbackParser.COMMAND_MAP.keys())

        # Ask AI to generate
        result = await self._call_nim_generate(description)
        if not result:
            return {"error": "Gagal generate fitur dari AI."}

        # Validate
        errors = self._validate_generated(result)
        if errors:
            return {"error": f"Validasi gagal: {', '.join(errors)}"}

        # Check conflicts
        cmd_name = f"!{result['feature_name']}"
        if cmd_name in existing:
            return {"error": f"Perintah `{cmd_name}` sudah ada."}

        return result

    async def _call_nim_generate(self, description: str) -> dict | None:
        """Call NIM API to generate feature code."""
        headers = {
            "Authorization": f"Bearer {os.environ.get('NVIDIA_NIM_API_KEY', '')}",
            "Content-Type": "application/json",
        }
        import httpx
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{os.environ.get('NVIDIA_NIM_BASE_URL', 'https://integrate.api.nvidia.com/v1')}/chat/completions",
                    headers=headers,
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [
                            {"role": "system", "content": FEATURE_GEN_PROMPT},
                            {"role": "user", "content": description[:1000]},
                        ],
                        "max_tokens": 4096,
                        "temperature": 0.2,
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                raw = data["choices"][0]["message"]["content"]
                # Extract JSON from markdown code block
                import re
                json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
                if json_match:
                    raw = json_match.group(1)
                return json.loads(raw)
        except Exception as e:
            logger.error(f"Feature generation failed: {e}")
            return None

    def _validate_generated(self, result: dict) -> list[str]:
        errors = []
        required = ["feature_name", "handler_code", "router_code", "yaml_entry"]
        for field in required:
            if field not in result:
                errors.append(f"Missing field: {field}")
        if not errors:
            fd = result.get("feature_name", "")
            handler = result.get("handler_code", "")
            if "async def handle_" not in handler:
                errors.append("Handler code must contain 'async def handle_'")
        return errors

    def backup_current_files(self) -> str:
        """Backup files before modification."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / ts
        backup_path.mkdir(parents=True, exist_ok=True)
        files_to_backup = [
            "agent/command_handler.py",
            "bot/command_router.py",
            "config/allowed_commands.yaml",
            "ai_module/fallback_parser.py",
        ]
        for rel_path in files_to_backup:
            src = Path.cwd() / rel_path
            if src.exists():
                shutil.copy2(src, backup_path / rel_path)
        return str(backup_path)

    async def install_feature(self, feature_data: dict, user_id: str) -> str:
        """Install generated feature into codebase with safety checks."""
        # 1. Backup
        backup_path = self.backup_current_files()

        # 2. Inject handler code
        self._inject_handler(feature_data["handler_code"])

        # 3. Inject router code
        self._inject_router(feature_data["feature_name"], feature_data["router_code"])

        # 4. Add YAML entry
        self._inject_yaml(feature_data["feature_name"], feature_data.get("yaml_entry", ""))

        # 5. Add fallback parser entry
        if feature_data.get("fallback_entry"):
            self._inject_fallback(feature_data["fallback_entry"])

        # 6. Register
        self.registry["features"].append({
            "name": feature_data["feature_name"],
            "description": feature_data.get("description", ""),
            "installed_at": datetime.now().isoformat(),
            "backup": backup_path,
            "installed_by": user_id,
        })
        self.registry["generated_count"] += 1
        self._save_registry()

        # 7. Syntax check
        try:
            subprocess.run(
                [sys.executable, "-m", "py_compile", "agent/command_handler.py"],
                capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            return f"❌ Syntax error setelah instalasi: {e.stderr[:500]}\nBackup tersimpan di: {backup_path}"

        return (
            f"✅ Fitur `{feature_data['feature_name']}` berhasil diinstal!\n"
            f"📝 Deskripsi: {feature_data.get('description', '-')}\n"
            f"🔙 Backup: {backup_path}\n"
            f"⚠️ Restart agent untuk mengaktifkan."
        )

    def _inject_handler(self, code: str):
        """Inject handler method into command_handler.py before the last method."""
        handler_path = Path.cwd() / "agent" / "command_handler.py"
        content = handler_path.read_text()
        # Find the last method (handle_*) or the end of class
        import re
        # Insert before the last helper function or at end of class
        insertion_point = content.rfind("    async def ")
        if insertion_point == -1:
            insertion_point = content.rfind("\n\n")
        # Insert after the last method, before any non-method code
        lines = content.split("\n")
        # Find a good insertion point - after the last method that starts with "    async def"
        last_method_end = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("async def handle_"):
                last_method_end = i
        # Find the next blank line after the last method
        for i in range(last_method_end, len(lines)):
            if lines[i].strip() == "":
                last_method_end = i
                break
        indented_code = "\n".join(f"    {line}" if line.strip() else "" for line in code.split("\n"))
        lines.insert(last_method_end + 1, indented_code)
        handler_path.write_text("\n".join(lines))
        logger.info(f"Handler injected: {len(code)} chars")

    def _inject_router(self, feature_name: str, code: str):
        """Inject router elif block into command_router.py before the else clause."""
        router_path = Path.cwd() / "bot" / "command_router.py"
        content = router_path.read_text()
        marker = "elif command_name == \"help\":"
        indented = "\n".join(f"            {line}" if line.strip() else "" for line in code.split("\n"))
        new_content = content.replace(
            f"            elif command_name == \"help\":",
            f"{indented}\n\n            elif command_name == \"help\":"
        )
        router_path.write_text(new_content)
        logger.info(f"Router injected for: {feature_name}")

    def _inject_yaml(self, feature_name: str, yaml_text: str):
        """Add YAML entry to allowed_commands.yaml."""
        yaml_path = Path.cwd() / "config" / "allowed_commands.yaml"
        content = yaml_path.read_text()
        # Insert before blocked_patterns
        marker = "\nblocked_patterns:"
        new_entry = f"\n  {feature_name}:\n    description: \"Auto-generated feature\"\n    requires_confirmation: false\n    sandbox_required: false\n"
        content = content.replace(marker, new_entry + marker)
        yaml_path.write_text(content)

    def _inject_fallback(self, entry_text: str):
        """Add fallback parser entry."""
        fallback_path = Path.cwd() / "ai_module" / "fallback_parser.py"
        content = fallback_path.read_text()
        # Insert before the closing of COMMAND_MAP
        marker = "COMMAND_MAP = {"
        insertion = f"{marker}\n{entry_text},"
        content = content.replace(marker, insertion, 1)
        fallback_path.write_text(content)

    def list_features(self) -> list[dict]:
        return self.registry.get("features", [])

# Singleton
self_feature_engine = SelfFeatureEngine()
```

#### Handler di `command_handler.py`:

```python
async def handle_create_feature(self, args: list[str]) -> str:
    from agent.self_feature import self_feature_engine
    if not args:
        return (
            "🧬 *Self-Feature Generation*\n"
            "`!create feature <deskripsi>` — Buat fitur baru\n"
            "`!create list` — Lihat fitur buatan sendiri\n"
        )
    if args[0].lower() == "list":
        features = self_feature_engine.list_features()
        if not features:
            return "Belum ada fitur kustom yang dibuat."
        lines = ["🧬 *Fitur Kustom Terinstal:*\n"]
        for f in features:
            lines.append(f"• `!{f['name']}` — {f['description']} ({f['installed_at'][:10]})")
        return "\n".join(lines)

    description = " ".join(args)
    # Step 1: Generate
    result = await self_feature_engine.generate_feature(description)
    if "error" in result:
        return f"❌ {result['error']}"
    # Step 2: Ask confirmation
    feature_name = result["feature_name"]
    return (
        f"🧬 *Generate Fitur Baru: `!{feature_name}`*\n\n"
        f"Deskripsi: {result.get('description', '-')}\n"
        f"Dependensi: {', '.join(result.get('dependencies', [])) or 'tidak ada'}\n\n"
        f"⚠️ Saya akan memodifikasi file:\n"
        f"• agent/command_handler.py\n"
        f"• bot/command_router.py\n"
        f"• config/allowed_commands.yaml\n"
        f"• ai_module/fallback_parser.py\n\n"
        f"Ketik `!create confirm {feature_name}` untuk melanjutkan,\n"
        f"atau `!create cancel` untuk membatalkan."
    )
```

---

### Fitur 3: MCP — Memory Context Provider

> **Command:** `!mcp [on|off|query|status]`  
> **File Baru:** `agent/memory/mcp_collector.py`

#### Konsep

MCP adalah background service yang **terus memantau** aktivitas laptop dan menyimpannya sebagai memory secara otomatis. Data yang dikumpulkan:

- Active window title (setiap 30 detik)
- File yang diakses/diedit (via file_watcher)
- Clipboard content (via smart_clipboard listener)
- Sistem metrics (CPU spikes, low memory)
- Calendar events (via Google Calendar)
- Browser tabs (via browser controller)
- Running proses significant (bukan sistem)

#### Implementasi

```python
# agent/memory/mcp_collector.py
"""
Memory Context Provider — Background collector.
Menyimpan konteks aktivitas user secara realtime ke MemoryStore.
"""
import os
import time
import asyncio
import platform
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
from agent.memory.manager import memory_manager

class MCPCollector:
    def __init__(self):
        self.active = False
        self._task = None
        self.interval = 30  # seconds between snapshots

    async def start(self):
        if self.active:
            return
        self.active = True
        self._task = asyncio.create_task(self._collect_loop())
        logger.info("🟢 MCP Collector started")

    async def stop(self):
        self.active = False
        if self._task:
            self._task.cancel()
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
        context = []

        # 1. Active window
        try:
            from agent.active_window import get_active_window
            win = get_active_window()
            if win:
                context.append(f"Active window: {win}")
        except Exception:
            pass

        # 2. System load
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            if cpu > 80 or ram > 85:
                context.append(f"High load: CPU={cpu}% RAM={ram}%")
        except Exception:
            pass

        # 3. Clipboard (if smart_clipboard is active)
        try:
            from agent.smart_clipboard import get_recent_clip
            clip = get_recent_clip()
            if clip:
                context.append(f"Clipboard content: {clip[:200]}")
        except Exception:
            pass

        # 4. Recent files
        try:
            from agent.recent_files import get_recent_files
            recent = get_recent_files(minutes=2)
            if recent:
                files_str = ", ".join(f.name for f in recent[:3])
                context.append(f"Recent files: {files_str}")
        except Exception:
            pass

        # Store non-empty context
        if context:
            text = " | ".join(context)
            memory_manager.remember(
                text=text,
                source="mcp",
                topic="context_snapshot",
                tags=["auto", "mcp"],
            )

    def get_recent_context(self, minutes: int = 10) -> str:
        """Get recent context summary for AI queries."""
        results = memory_manager.search(
            query="context_snapshot recent activity",
            k=10,
            topic="context_snapshot",
        )
        if not results:
            return "No recent context available."
        lines = ["📋 *Recent Context:*\n"]
        for r in results:
            ts = r["metadata"].get("timestamp", "")[11:19]
            lines.append(f"[{ts}] {r['text'][:150]}")
        return "\n".join(lines)

# Singleton
mcp_collector = MCPCollector()
```

#### Query Handler:

```python
# Agent command_handler
async def handle_mcp(self, args: list[str]) -> str:
    from agent.memory.mcp_collector import mcp_collector
    if not args:
        return (
            "🧠 *Memory Context Provider (MCP)*\n"
            "`!mcp on` — Aktifkan monitoring otomatis\n"
            "`!mcp off` — Nonaktifkan\n"
            "`!mcp status` — Status collector\n"
            "`!mcp query [pertanyaan]` — Tanya konteks saat ini\n"
        )
    sub = args[0].lower()
    if sub == "on":
        await mcp_collector.start()
        return "🟢 MCP Collector diaktifkan. Monitoring setiap 30 detik."
    elif sub == "off":
        await mcp_collector.stop()
        return "🔴 MCP Collector dinonaktifkan."
    elif sub == "status":
        return f"{'🟢 Aktif' if mcp_collector.active else '🔴 Nonaktif'}"
    elif sub == "query":
        query = " ".join(args[1:])
        context = mcp_collector.get_recent_context()
        if query:
            results = memory_manager.search(query, k=5)
            if results:
                context += "\n\n🔍 *Memory Search:*\n" + "\n".join(
                    f"• {r['text'][:200]}" for r in results
                )
        return context or "Tidak ada konteks tersedia."
    return "❌ Subperintah tidak dikenal."
```

---

### Fitur 4: Personal Virtual Companion

> **Command:** `!companion <pesan>`  
> **File Baru:** `agent/companion.py`, `agent/companion_mood.py`

#### Alur

```
User: "!companion capek banget hari ini"
  → CompanionHandler.process("capek banget hari ini")
  → MemoryManager.search("capek hari ini") → dapat konteks
  → NIM API with companion system prompt
  → Response: empati + saran + motivasi
  → MemoryManager.remember(response, source="companion")
```

#### Implementasi

```python
# agent/companion.py
"""
Personal Virtual Companion — Emotional AI assistant.
"""
import os
import json
import httpx
from datetime import datetime
from loguru import logger

COMPANION_PROMPT = """Kamu adalah asisten virtual sekaligus teman yang peduli.
Tugasmu:
1. Ingat semua percakapan sebelumnya dengan user (diberikan sebagai konteks)
2. Pahami perasaan dan mood user
3. Beri dukungan emosional, motivasi, dan saran yang hangat
4. Gunakan bahasa Indonesia yang natural dan ramah
5. Jika user sedang stres/sedih → beri empati dulu, baru saran
6. Jika user senang → rayakan bersama
7. Respond in Indonesian unless user speaks English

Gunakan konteks berikut dari memory untuk personalisasi:
{memory_context}

Percakapan terakhir user: {user_input}
"""

class Companion:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get(
            "NVIDIA_NIM_BASE_URL",
            "https://integrate.api.nvidia.com/v1"
        )
        self.model = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")

    async def chat(self, user_input: str, user_id: str) -> str:
        """Process companion chat with context."""
        # Get memory context
        try:
            from agent.memory.manager import memory_manager
            memory_results = memory_manager.search(user_input, k=5)
            memory_context = "\n".join(
                f"- {r['text'][:200]}" for r in memory_results
            ) if memory_results else "Tidak ada riwayat sebelumnya."
        except Exception:
            memory_context = "Tidak ada riwayat sebelumnya."

        prompt = COMPANION_PROMPT.format(
            memory_context=memory_context,
            user_input=user_input,
        )

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.nim_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": user_input[:1000]},
                        ],
                        "max_tokens": 512,
                        "temperature": 0.7,
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                response = data["choices"][0]["message"]["content"].strip()

                # Save to memory
                try:
                    memory_manager.remember(
                        f"Companion chat: User said '{user_input[:100]}'. AI replied: '{response[:200]}'",
                        source="companion",
                        topic="personal_chat",
                        tags=["companion", "chat"],
                    )
                except Exception:
                    pass

                return response

        except httpx.TimeoutException:
            return "Maaf, saya agak lambat merespon. Coba ulangi lagi ya? 🙏"
        except Exception as e:
            logger.error(f"Companion error: {e}")
            return "Maaf, aku sedang error. Coba lagi nanti ya. 🤗"

companion = Companion()
```

---

### Fitur 5: Advanced Problem Solver

> **Command:** `!solve <problem>`  
> **File Baru:** `agent/solver.py`

#### Alur

```
User: "!solve CUDA out of memory PyTorch"
  → SolverEngine.solve("CUDA out of memory PyTorch")
  → MemoryManager.search("CUDA out of memory") → cached solution?
  → If yes → return cached
  → If no → web search (scraping + summarization)
  → NIM summarize hasil web → solution steps
  → MemoryManager.remember(solution)
  → Return ke user
```

```python
# agent/solver.py
"""
Advanced Problem Solver with live web access and memory cache.
"""
import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

SOLVER_PROMPT = """Kamu adalah problem solver expert. User punya masalah berikut:

PROBLEM: {problem}

Hasil pencarian web terkait:
{web_results}

Tugasmu:
1. Analisis masalah berdasarkan konteks yang diberikan
2. Berikan 3-5 langkah solusi yang konkret dan actionable
3. Prioritaskan solusi yang paling mungkin berhasil
4. Sertakan command/code jika relevan (dalam code block)
5. Jika ada risiko, beri peringatan
6. Gunakan bahasa Indonesia

Format response:
🔍 **Analisis:** [analisis singkat masalah]
📋 **Solusi:**
1. [langkah 1]
2. [langkah 2]
...

⚠️ **Peringatan:** [jika ada]
"""

class SolverEngine:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get(
            "NVIDIA_NIM_BASE_URL",
            "https://integrate.api.nvidia.com/v1"
        )

    async def solve(self, problem: str) -> str:
        # 1. Check memory cache first
        try:
            cached = memory_manager.search(problem, k=3, topic="solved_problems")
            for c in cached:
                if c["distance"] < 0.15:  # very close match
                    ts = c["metadata"].get("timestamp", "")[:10]
                    return (
                        f"📦 *Solusi dari memory (cache {ts}):*\n\n"
                        f"{c['text']}"
                    )
        except Exception:
            pass

        # 2. Web search for solutions
        web_results = await self._search_web(problem)

        # 3. AI summarize + solve
        result = await self._call_solver_nim(problem, web_results)

        # 4. Cache the solution
        try:
            memory_manager.remember(
                f"Solved problem: {problem}\nSolution: {result[:500]}",
                source="solver",
                topic="solved_problems",
                tags=["problem_solved", "solver"],
            )
        except Exception:
            pass

        return result

    async def _search_web(self, query: str) -> str:
        """Web search using existing scraper."""
        try:
            from agent.scraper import search_and_scrape
            results = await search_and_scrape(query, max_results=3)
            return results[:2000]
        except Exception:
            return "Web search unavailable."

    async def _call_solver_nim(self, problem: str, web_results: str) -> str:
        prompt = SOLVER_PROMPT.format(problem=problem, web_results=web_results[:2000])
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.nim_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1024,
                        "temperature": 0.3,
                    }
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"❌ Error AI: {e}"

solver = SolverEngine()
```

---

### Fitur 6: Daily Self-Introspection & Auto Evolution

> **Command:** `!self evolve` (otomatis tiap malam)  
> **File Baru:** `agent/evolution.py`

#### Alur (Midnight Cron)

```
  ┌─ setiap pukul 00:00 ─────────────────────────────┐
  │                                                    │
  │  1. Analyze performance metrics                   │
  │  2. Check error logs (watchdog + audit)           │
  │  3. Profile slow commands (>5s execution)          │
  │  4. Suggest optimizations                          │
  │  5. Auto-fix simple bugs (typos, imports)         │
  │  6. Generate evolution report                      │
  │  7. Push ke user via scheduler alert              │
  │                                                    │
  └────────────────────────────────────────────────────┘
```

```python
# agent/evolution.py
"""
Self-Evolution Engine — daily introspection & auto improvement.
"""
import os
import json
import asyncio
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

EVOLUTION_LOG = Path.home() / ".config" / "rav-remote" / "evolution" / "log.json"

class EvolutionEngine:
    def __init__(self):
        EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        self._load_log()

    def _load_log(self):
        if EVOLUTION_LOG.exists():
            with open(EVOLUTION_LOG) as f:
                self.log = json.load(f)
        else:
            self.log = {"evolutions": [], "total_fixes": 0, "total_optimizations": 0}

    def _save_log(self):
        with open(EVOLUTION_LOG, "w") as f:
            json.dump(self.log, f, indent=2)

    async def run_evolution(self) -> str:
        """Run full evolution cycle."""
        report_parts = []
        fixes = []

        # 1. Analyze error logs
        try:
            error_analysis = await self._analyze_errors()
            if error_analysis:
                report_parts.append(error_analysis)
        except Exception as e:
            logger.error(f"Error analysis failed: {e}")

        # 2. Profile command performance
        try:
            perf_analysis = await self._profile_performance()
            if perf_analysis:
                report_parts.append(perf_analysis)
        except Exception as e:
            logger.error(f"Performance profiling failed: {e}")

        # 3. Auto-fix simple issues
        try:
            fix_results = await self._auto_fix()
            if fix_results:
                fixes.extend(fix_results)
                report_parts.append(f"🔧 *Auto Fixes ({len(fixes)}):*\n" + "\n".join(fixes))
        except Exception as e:
            logger.error(f"Auto fix failed: {e}")

        # 4. Optimize prompts
        try:
            prompt_opt = await self._optimize_prompts()
            if prompt_opt:
                report_parts.append(prompt_opt)
        except Exception as e:
            logger.error(f"Prompt optimization failed: {e}")

        # 5. Log evolution
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fixes": fixes,
            "report": report_parts,
        }
        self.log["evolutions"].append(entry)
        self.log["total_fixes"] += len(fixes)
        self._save_log()

        # 6. Generate report
        report = "🧬 *Self-Evolution Report*\n"
        if report_parts:
            report += "\n" + "\n\n".join(report_parts)
        else:
            report += "Semua sistem dalam kondisi baik. Tidak ada perubahan yang diperlukan."
        return report

    async def _analyze_errors(self) -> str | None:
        """Analyze watchdog and audit logs for error patterns."""
        # Read audit log for ERROR entries today
        audit_path = Path(os.environ.get("LOG_FILE", "./logs/audit.log"))
        if not audit_path.exists():
            return None
        content = audit_path.read_text().split("\n")
        today = datetime.now().strftime("%Y-%m-%d")
        errors = [l for l in content if today in l and ("ERROR" in l or "CRITICAL" in l)]
        if not errors:
            return "✅ Tidak ada error hari ini."
        return f"📊 Error hari ini: {len(errors)} entri\n  (cek `!activity log` untuk detail)"

    async def _profile_performance(self) -> str | None:
        """Profile command execution times from audit logs."""
        audit_path = Path(os.environ.get("LOG_FILE", "./logs/audit.log"))
        if not audit_path.exists():
            return None
        return "⏱️ Performance baseline: normal"

    async def _auto_fix(self) -> list[str]:
        """Auto-fix simple issues (imports, typos, config)."""
        fixes = []
        # Check Python syntax
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", "agent/command_handler.py"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                logger.warning(f"Syntax error detected: {result.stderr[:200]}")
        except Exception:
            pass
        return fixes

    async def _optimize_prompts(self) -> str | None:
        """Analyze and optimize AI prompts based on usage."""
        return None

    def get_history(self, days: int = 7) -> str:
        """Get evolution history."""
        entries = self.log["evolutions"][-days:]
        if not entries:
            return "Belum ada riwayat evolusi."
        lines = ["🧬 *Evolution History:*\n"]
        for e in entries:
            ts = e["timestamp"][:10]
            fixes = len(e.get("fixes", []))
            lines.append(f"• {ts}: {fixes} fixes, {len(e.get('report', []))} reports")
        return "\n".join(lines)

evolution_engine = EvolutionEngine()
```

---

### Fitur 7: Personalized Usage Optimization Advisor

> **Command:** `!optimize me`  
> **File Baru:** `agent/analytics.py`, `agent/optimizer.py`

#### Alur

```
1. Kumpulkan data penggunaan dari:
   - Audit logs (command frequency per time)
   - Time tracker (project hours)
   - Focus mode sessions
   - Feature usage frequency
   - Error rates per command
2. Analisis pola dengan AI
3. Berikan rekomendasi personal
```

```python
# agent/analytics.py
"""
Usage Analytics Collector.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

ANALYTICS_FILE = Path.home() / ".config" / "rav-remote" / "analytics" / "usage.json"

class UsageAnalytics:
    def __init__(self):
        ANALYTICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if ANALYTICS_FILE.exists():
            with open(ANALYTICS_FILE) as f:
                self.data = json.load(f)
        else:
            self.data = {
                "command_counts": {},
                "hourly_usage": {str(h): 0 for h in range(24)},
                "feature_frequency": {},
                "daily_active_days": [],
            }

    def _save(self):
        with open(ANALYTICS_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def record_command(self, command_name: str):
        """Record a command execution."""
        hour = datetime.now().hour
        self.data["command_counts"][command_name] = self.data["command_counts"].get(command_name, 0) + 1
        self.data["hourly_usage"][str(hour)] = self.data["hourly_usage"].get(str(hour), 0) + 1
        self._save()

    def get_peak_hours(self) -> list[int]:
        """Get top 3 most active hours."""
        sorted_hours = sorted(
            self.data["hourly_usage"].items(),
            key=lambda x: -x[1]
        )
        return [int(h) for h, _ in sorted_hours[:3]]

    def get_most_used_features(self, limit: int = 5) -> list[tuple[str, int]]:
        sorted_cmds = sorted(
            self.data["command_counts"].items(),
            key=lambda x: -x[1]
        )
        return [(c, n) for c, n in sorted_cmds[:limit]]

    def get_unused_features(self, all_features: set[str]) -> list[str]:
        used = set(self.data["command_counts"].keys())
        return [f for f in all_features if f not in used]

usage_analytics = UsageAnalytics()
```

```python
# agent/optimizer.py
"""
Personalized Usage Optimization Advisor.
"""
from agent.analytics import usage_analytics

class Optimizer:
    async def generate_advice(self) -> str:
        peak = usage_analytics.get_peak_hours()
        top_features = usage_analytics.get_most_used_features(5)
        lines = ["📊 *Usage Optimization Advice*\n"]

        if peak:
            hours_str = ", ".join(f"{h}:00" for h in peak)
            lines.append(f"⏰ Kamu paling aktif jam {hours_str}")
            lines.append(f"💡 Saran: Set `!focus` otomatis jam {peak[0]}:00 dengan `!schedule`")

        if top_features:
            lines.append(f"\n🔥 Fitur favorit:")
            for cmd, count in top_features:
                lines.append(f"  • `!{cmd}` — {count}x digunakan")

        lines.append(f"\n📈 Tips produktivitas:")
        lines.append(f"  • Gunakan `!workspace save` untuk menyimpan sesi kerja")
        lines.append(f"  • Coba `!daily` untuk lihat aktivitas harian")
        lines.append(f"  • Aktifkan `!focus` untuk mode Pomodoro")

        return "\n".join(lines)

optimizer = Optimizer()
```

---

### Fitur 8: Proactive & Reactive Awareness

> **Command:** `!proactive [on|off|status]`  
> **File Baru:** `agent/proactive.py`

#### Alur

```
Background service yang tiap 5 menit:
  1. Cek apakah ada context penting dari MCP
  2. Jika user sedang mengerjakan laporan → "Butuh bantuan?"
  3. Jika CPU tinggi + banyak proses → "Mau saya bersihkan?"
  4. Jika ada memory relevan → "Ingat tentang project X?"
  5. Kirim sebagai scheduler alert
```

```python
# agent/proactive.py
"""
Proactive Awareness Engine.
"""
import asyncio
import psutil
from datetime import datetime
from loguru import logger
from agent.memory.manager import memory_manager
from agent.memory.mcp_collector import mcp_collector

class ProactiveEngine:
    def __init__(self):
        self.active = False
        self._task = None
        self.check_interval = 300  # 5 minutes

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
            self._task = None
        logger.info("🔴 Proactive Engine stopped")

    async def _proactive_loop(self):
        while self.active:
            try:
                alert = await self._check_context()
                if alert:
                    from agent.command_handler import proactive_alerts
                    proactive_alerts.append(alert)
            except Exception as e:
                logger.debug(f"Proactive check error: {e}")
            await asyncio.sleep(self.check_interval)

    async def _check_context(self) -> str | None:
        alerts = []

        # 1. Active window analysis
        try:
            from agent.active_window import get_active_window
            win = get_active_window()
            if win and any(kw in win.lower() for kw in ["report", "laporan", "dokumen", "paper", "skripsi", "tugas"]):
                alerts.append(f"📝 Detected: `{win}`, need help summarizing?")
        except Exception:
            pass

        # 2. High resource usage
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            if cpu > 85 or ram > 90:
                alerts.append(f"⚠️ High load detected (CPU={cpu}%, RAM={ram}%). Run `!process list`?")
        except Exception:
            pass

        # 3. Idle detection
        try:
            if psutil.cpu_percent(interval=0.1) < 5 and not mcp_collector.active:
                alerts.append("💤 Seems idle. Activate `!mcp on` for context monitoring?")
        except Exception:
            pass

        return alerts[0] if alerts else None

proactive_engine = ProactiveEngine()
```

---

### Fitur 9: Continuous Knowledge Enrichment

> **Command:** `!learn <topic>`  
> **File Baru:** `agent/knowledge.py`

#### Alur

```
User: "!learn AI Agent 2026"
  → KnowledgeEngine.fetch("AI Agent 2026")
  → Web search + scrape top 3 articles
  → AI summarize each article
  → Save to knowledge base (JSON + vector)
  → MemoryManager.remember(summary)
  → Return: "✅ Saved 3 articles about AI Agent 2026"
```

```python
# agent/knowledge.py
"""
Continuous Knowledge Enrichment Engine.
"""
import os
import json
import httpx
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
from agent.memory.manager import memory_manager

KNOWLEDGE_DIR = Path.home() / ".config" / "rav-remote" / "knowledge"

class KnowledgeEngine:
    def __init__(self):
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        self.index_file = KNOWLEDGE_DIR / "index.json"
        self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            with open(self.index_file) as f:
                self.index = json.load(f)
        else:
            self.index = {"topics": {}, "total_articles": 0}

    def _save_index(self):
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)

    async def learn(self, topic: str) -> str:
        """Research a topic and save to knowledge base."""
        # 1. Web search
        articles = await self._search_articles(topic)
        if not articles:
            return f"❌ Tidak menemukan artikel tentang '{topic}'."

        # 2. Summarize each
        saved = []
        for i, article in enumerate(articles[:3]):
            summary = await self._summarize_article(article, topic)
            if summary:
                # Save to file
                safe_name = topic.lower().replace(" ", "_")[:30]
                fname = KNOWLEDGE_DIR / f"{safe_name}_{i}.json"
                entry = {
                    "topic": topic,
                    "source": article.get("url", ""),
                    "title": article.get("title", ""),
                    "summary": summary,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
                with open(fname, "w") as f:
                    json.dump(entry, f, indent=2)
                saved.append(article.get("title", f"Article {i+1}"))

                # Save to memory
                memory_manager.remember(
                    f"Knowledge: {topic} — {summary[:300]}",
                    source="knowledge",
                    topic=topic,
                    tags=["knowledge", "learned"],
                )

        # Update index
        self.index["topics"][topic] = self.index["topics"].get(topic, 0) + len(saved)
        self.index["total_articles"] += len(saved)
        self._save_index()

        return (
            f"📚 *Knowledge Enriched: {topic}*\n"
            f"✅ {len(saved)} artikel disimpan:\n" +
            "\n".join(f"  • {s}" for s in saved) +
            f"\n\nTotal knowledge base: {self.index['total_articles']} articles"
        )

    async def _search_articles(self, topic: str) -> list[dict]:
        """Search web for articles."""
        try:
            from agent.scraper import search_web
            return await search_web(topic, max_results=3)
        except Exception:
            return []

    async def _summarize_article(self, article: dict, topic: str) -> str | None:
        """Summarize article using NIM."""
        text = article.get("content", article.get("snippet", ""))[:3000]
        if not text:
            return None

        prompt = f"""Summarize the following article about '{topic}' in 3-5 bullet points in Indonesian.
        Focus on key insights, trends, and actionable information.

        Article: {text}"""

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{os.environ.get('NVIDIA_NIM_BASE_URL', 'https://integrate.api.nvidia.com/v1')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.environ.get('NVIDIA_NIM_API_KEY', '')}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 512,
                        "temperature": 0.3,
                    }
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Summarize error: {e}")
            return None

    def list_topics(self) -> str:
        if not self.index["topics"]:
            return "Knowledge base kosong. Gunakan `!learn <topik>` untuk mengisi."
        lines = ["📚 *Knowledge Base Topics:*\n"]
        for topic, count in sorted(self.index["topics"].items(), key=lambda x: -x[1]):
            lines.append(f"  • {topic}: {count} artikel")
        return "\n".join(lines)

knowledge_engine = KnowledgeEngine()
```

---

### Fitur 10: Advanced Autonomous Agent Mode

> **Command:** `!agent <goal> [duration]`  
> **File Baru:** `agent/autonomous_agent.py`

#### Alur

```
User: "!agent Siapkan presentasi mingguan + update data sales"
  → AutonomousAgent.run(goal)
  → Planner: breakdown goal → sub-tasks
  → Execute sub-tasks sequentially:
     ├── !daily → get activity data
     ├── !ai research "sales data format presentasi"
     ├── !ai write presentasi "mingguan sales"
     ├── !get presentasi.pptx → upload ke user
  → Report hasil
```

```python
# agent/autonomous_agent.py
"""
Advanced Autonomous Agent — menerima goal kompleks, membuat rencana,
mengeksekusi sub-tugas secara otonom menggunakan semua fitur existing.
"""
import os
import json
import asyncio
import httpx
from datetime import datetime, timezone
from loguru import logger
from bot.command_router import CommandRouter

AUTONOMOUS_PROMPT = """Kamu adalah Autonomous Agent Planner untuk RAV-REMOTE.
User memberikan goal berikut:

GOAL: {goal}

Tugasmu adalah membuat rencana eksekusi dalam bentuk daftar langkah.
Setiap langkah harus menggunakan perintah RAV-REMOTE yang sudah ada.

PERINTAH TERSEDIA:
- !screenshot, !video, !webcam — Media capture
- !sysinfo, !battery, !brightness — System info
- !ls, !get, !find — File navigation
- !web [query] — Web search
- !ai work/write/automate/summarize/research/insight — AI tasks
- !daily — Daily activity report
- !focus, !reminder, !task, !todo — Productivity
- !memory search — Search memory
- !solve [problem] — Problem solving
- !companion — Chat with companion
- !learn [topic] — Knowledge enrichment
- !scrape [url] — Web scraping

RESPON JSON:
```json
{{
  "plan": [
    {{"step": 1, "command": "!screenshot", "reason": "..."}},
    {{"step": 2, "command": "!ai research ...", "reason": "..."}}
  ],
  "estimated_duration": "5 menit",
  "risk_level": "low|medium|high"
}}
```
"""

class AutonomousAgent:
    def __init__(self):
        self.router = CommandRouter()
        self.running = False

    async def run(self, goal: str, user_id: str) -> str:
        """Run autonomous agent for a given goal."""
        self.running = True
        try:
            # 1. Generate plan
            plan = await self._generate_plan(goal)
            if not plan or "plan" not in plan:
                return "❌ Gagal membuat rencana untuk goal tersebut."

            # 2. Execute each step
            results = []
            for step in plan["plan"]:
                if not self.running:
                    results.append("⏹️ Agent dihentikan oleh user.")
                    break
                cmd = step["command"]
                reason = step.get("reason", "")
                results.append(f"📌 *Step {step['step']}:* {reason}\n`{cmd}`")
                try:
                    result = await self.router.route(cmd, user_id)
                    if isinstance(result, str):
                        results.append(f"  {result[:300]}")
                    elif isinstance(result, dict):
                        results.append(f"  ✅ {result.get('type', 'success')}")
                    else:
                        results.append(f"  ✅ Done")
                except Exception as e:
                    results.append(f"  ❌ Error: {e}")

                await asyncio.sleep(0.5)  # rate limit between steps

            # 3. Final report
            report = (
                f"🤖 *Autonomous Agent Report*\n"
                f"Goal: {goal}\n"
                f"Status: ✅ Completed\n"
                f"Steps: {len(plan.get('plan', []))}\n\n"
            )
            report += "\n".join(results)

            # Save to memory
            try:
                from agent.memory.manager import memory_manager
                memory_manager.remember(
                    f"Autonomous agent completed goal: {goal}\nResults: {report[:500]}",
                    source="autonomous_agent",
                    topic="agent_execution",
                    tags=["autonomous", "agent"],
                )
            except Exception:
                pass

            return report

        finally:
            self.running = False

    async def _generate_plan(self, goal: str) -> dict | None:
        """Generate execution plan using NIM."""
        prompt = AUTONOMOUS_PROMPT.format(goal=goal)
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{os.environ.get('NVIDIA_NIM_BASE_URL', 'https://integrate.api.nvidia.com/v1')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.environ.get('NVIDIA_NIM_API_KEY', '')}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 2048,
                        "temperature": 0.3,
                    }
                )
                resp.raise_for_status()
                raw = resp.json()["choices"][0]["message"]["content"]
                import re
                json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                return json.loads(raw)
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            return None

    def stop(self):
        self.running = False

autonomous_agent = AutonomousAgent()
```

---

## 5. Modifikasi File Existing

| File | Modifikasi |
|------|-----------|
| `requirements.txt` | Tambah `chromadb`, `sentence-transformers` |
| `agent/main.py` | Warmup embedding model, init MCP, init Proactive |
| `agent/command_handler.py` | 10 handler baru (`handle_memory`, `handle_mcp`, `handle_companion`, `handle_solve`, `handle_create_feature`, `handle_self_evolve`, `handle_optimize_me`, `handle_proactive`, `handle_learn`, `handle_agent`) |
| `bot/command_router.py` | 10 `elif` route baru + import statements |
| `config/allowed_commands.yaml` | 10 entri baru + alias |
| `ai_module/fallback_parser.py` | 10+ entri di `COMMAND_MAP` |
| `ai_module/prompt_templates.py` | Tambah command baru di SYSTEM_PROMPT |
| `ai_module/nim_client.py` | Handle command baru di `_validate_ai_output` |
| `security/audit_logger.py` | Pastikan semua feature baru ter-log (existing pattern sudah support) |
| `security/sanitizer.py` | Tidak perlu modifikasi — sudah generic |

---

## 6. File Baru

```
agent/
├── memory/
│   ├── __init__.py
│   ├── store.py          # ChromaDB CRUD
│   ├── embeddings.py     # Sentence-transformers
│   ├── manager.py        # MemoryManager orchestrator
│   ├── mcp_collector.py  # MCP background collector
│   └── sync.py           # Cross-device sync
├── companion.py           # Personal Virtual Companion
├── companion_mood.py      # Mood tracking
├── solver.py              # Advanced Problem Solver
├── self_feature.py        # Self-Feature Generation
├── evolution.py           # Self-Evolution Engine
├── analytics.py           # Usage analytics
├── optimizer.py           # Usage optimization advisor
├── proactive.py           # Proactive awareness engine
├── knowledge.py           # Knowledge enrichment
├── autonomous_agent.py    # Autonomous Agent mode
└── safe_backup.py         # Backup before code modification
```

Total file baru: **18**

---

## 7. Daftar Dependensi Baru

### requirements.txt

```txt
# AI Memory & Vector Database
chromadb==1.10.0
sentence-transformers==3.4.0
```

**Catatan:** `chromadb` akan otomatis menginstal `numpy`, `onnxruntime`, `tokenizers`, `hnswlib`.

### Perkiraan Tambahan Disk

- `sentence-transformers` + `all-MiniLM-L6-v2`: ~90MB
- `chromadb`: ~30MB
- Total: ~120MB tambahan

---

## 8. Strategi Testing

### Unit Tests (18 test files baru)

| Test | Lokasi | Cakupan |
|------|--------|---------|
| Memory embedding | `tests/test_memory_embed.py` | embed(), embed_batch(), dimension |
| Memory store CRUD | `tests/test_memory_store.py` | add, search, delete, stats |
| Memory chunking | `tests/test_memory_chunk.py` | _chunk_text(), overlap logic |
| MCP collector | `tests/test_mcp.py` | collect logic, formatting |
| Companion chat | `tests/test_companion.py` | prompt format, context injection |
| Solver engine | `tests/test_solver.py` | solve flow, cache check |
| Self-feature gen | `tests/test_self_feature.py` | validation, injection |
| Evolution engine | `tests/test_evolution.py` | analysis, auto-fix logic |
| Analytics | `tests/test_analytics.py` | record, peak hours, top features |
| Optimizer | `tests/test_optimizer.py` | advice generation |
| Proactive engine | `tests/test_proactive.py` | context check, alert formatting |
| Knowledge engine | `tests/test_knowledge.py` | learn, summarize, index |
| Autonomous agent | `tests/test_autonomous.py` | plan generation, step execution |
| Integration | `tests/test_memory_integration.py` | full memory pipeline |
| Integration | `tests/test_ai_pipeline.py` | companion + solver + knowledge |

### Integration Test Pattern

```python
# tests/test_memory_integration.py
import pytest
from agent.memory.manager import memory_manager

@pytest.mark.asyncio
async def test_memory_pipeline():
    # 1. Store
    memory_manager.remember(
        "Test memory content untuk unit test",
        source="test",
        topic="testing",
        tags=["test"],
    )

    # 2. Search
    results = memory_manager.search("test memory")
    assert len(results) > 0
    assert "test" in results[0]["metadata"]["tags"]

    # 3. Stats
    stats = memory_manager.store.stats()
    assert stats["total_entries"] > 0

    # 4. Cleanup (if needed)
    for r in results:
        memory_manager.store.delete(r["id"])
```

### Manual Testing Checklist

```
[ ] !memory search "test" → returns results
[ ] !memory stats → show counts
[ ] !mcp on → background collector active
[ ] !mcp query "apa yang sedang dikerjakan" → context
[ ] !companion "halo" → chat response with empathy
[ ] !solve "error python import" → solution steps
[ ] !create feature "test feature" → generates code
[ ] !self evolve → evolution report
[ ] !optimize me → usage advice
[ ] !proactive on → proactive alerts
[ ] !learn "python tips" → knowledge saved
[ ] !agent "cek sistem info" → autonomous execution
```

---

## 9. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| ChromaDB corrupt | Memory hilang | JSON index backup tiap 24 jam |
| Embedding model OOM | Agent crash | Lazy loading + fallback if RAM < 2GB |
| NIM API timeout | Semua fitur lambat | Timeout 45s + graceful fallback message |
| Self-feature breaks code | Agent error | Backup sebelum modifikasi + syntax check |
| Knowledge base too large | Disk penuh | Max 500 articles, auto-prune tertua |
| Proactive spams user | User annoyance | Max 1 proactive alert per 30 menit |
| Autonomous agent infinite loop | Resource drain | Max 10 steps per execution, timeout 5 menit |
| Companion mood detection wrong | Awkward response | Conservative empathy, fallback "Ada yang bisa dibantu?" |
| Cross-device sync conflict | Memory inconsistency | Timestamp-based conflict resolution (newest wins) |
| ChromaDB version mismatch | Dependency hell | Pin exact version in requirements.txt |

---

## Ringkasan Final

| Metrik | Value |
|--------|-------|
| Fitur baru | 10 |
| File baru | ~18 files |
| File dimodifikasi | ~10 files |
| Baris kode baru (estimasi) | ~3,500-4,500 lines |
| Dependensi baru | 2 (chromadb, sentence-transformers) |
| Tambahan disk | ~120MB |
| Total estimasi implementasi | 6 minggu (paralel: 3-4 minggu) |
| Prioritas | P0-P4 (lihat dependency graph) |
| Risiko utama | ChromaDB stability, embedding model RAM usage |

---

> **Catatan:** Dokumen ini adalah **living plan**. Update sesuai progres implementasi dan feedback dari hasil testing setiap fase.
