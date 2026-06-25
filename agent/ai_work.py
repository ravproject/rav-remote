"""
AI Work Module — AI-powered productivity, writing, automation, summarization, research, insight.
"""
import os
import json
import asyncio
import httpx
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

AI_WORK_DIR = Path.home() / "Documents" / "RAV-AI-Work"
AI_RESEARCH_DIR = Path.home() / "Documents" / "RAV-Research"

NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
NIM_BASE_URL = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-8b-instruct")

class NIMCallError(Exception):
    """Exception raised when an NVIDIA NIM API call fails."""
    pass

async def _call_nim(prompt: str, system_prompt: str = None, max_tokens: int = 500) -> str:
    if not NIM_API_KEY:
        raise NIMCallError("AI tidak tersedia: NVIDIA_NIM_API_KEY tidak di-set.")
    headers = {
        "Authorization": f"Bearer {NIM_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt[:2000]})
    payload = {
        "model": NIM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(f"{NIM_BASE_URL}/chat/completions", headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        try:
            body = e.response.text[:500]
        except Exception:
            body = ""
        logger.error(f"NIM HTTP {e.response.status_code}: {body}")
        raise NIMCallError(f"Gagal memanggil AI: HTTP {e.response.status_code} - {body[:200]}")
    except httpx.TimeoutException:
        logger.error("NIM API timeout after 60s")
        raise NIMCallError("Gagal memanggil AI: Timeout (API tidak merespon dalam 60 detik)")
    except httpx.ConnectError as e:
        logger.error(f"NIM connection error: {e}")
        raise NIMCallError(f"Gagal memanggil AI: Gagal terhubung ke {NIM_BASE_URL}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"NIM response parse error: {type(e).__name__}: {e}")
        raise NIMCallError(f"Gagal memanggil AI: Respon API tidak sesuai format ({type(e).__name__})")
    except Exception as e:
        logger.opt(exception=True).error(f"NIM unexpected error")
        raise NIMCallError(f"Gagal memanggil AI: {repr(e)}")

async def ai_work(task: str) -> str:
    try:
        system = "Kamu adalah asisten produktivitas. Jawab dengan ringkas dan actionable."
        result = await _call_nim(task, system, max_tokens=800)
        AI_WORK_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = AI_WORK_DIR / f"ai_work_{ts}.md"
        with open(filepath, "w") as f:
            f.write(f"# AI Work: {task}\n\nDate: {datetime.now().isoformat()}\n\n{result}\n")
        return f"✅ {result}\n\n📁 Disimpan: {filepath}"
    except NIMCallError as e:
        return str(e)

async def ai_write(doc_type: str, topic: str) -> str:
    try:
        system = f"Kamu adalah asisten menulis. Buatkan {doc_type} profesional dalam Bahasa Indonesia."
        prompt = f"Buatkan {doc_type} tentang: {topic}"
        result = await _call_nim(prompt, system, max_tokens=1000)
        AI_WORK_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        safe_type = "".join(c for c in doc_type if c.isalnum() or c in " _-") or "dokumen"
        filepath = AI_WORK_DIR / f"{ts}_{safe_type}_{topic[:20].replace(' ', '_')}.md"
        with open(filepath, "w") as f:
            f.write(f"# {doc_type}: {topic}\n\nDate: {datetime.now().isoformat()}\n\n{result}\n")
        return f"✅ Draft {doc_type} selesai:\n\n{result}\n\n📁 {filepath}"
    except NIMCallError as e:
        return str(e)

def _load_registry() -> list:
    registry_path = Path.home() / "safe_scripts" / "registry.json"
    if registry_path.exists():
        try:
            with open(registry_path, "r") as f:
                items = json.load(f)
            valid_items = []
            changed = False
            for item in items:
                script_file = Path.home() / "safe_scripts" / item["filename"]
                if script_file.exists():
                    valid_items.append(item)
                else:
                    changed = True
            if changed:
                try:
                    with open(registry_path, "w") as f:
                        json.dump(valid_items, f, indent=2)
                except Exception as e:
                    logger.error(f"Failed to update registry: {e}")
            return valid_items
        except Exception:
            return []
    return []

def _save_registry(registry: list):
    registry_path = Path.home() / "safe_scripts" / "registry.json"
    try:
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save registry: {e}")

async def ai_automate(description: str) -> str:
    try:
        registry = _load_registry()
        
        # Check for similar script in registry
        import re
        norm_desc = re.sub(r'\s+', ' ', description.strip().lower())
        
        best_match = None
        for item in registry:
            item_desc = re.sub(r'\s+', ' ', item['description'].strip().lower())
            if norm_desc == item_desc:
                best_match = item
                break
        
        if not best_match:
            words = set(w for w in norm_desc.split() if len(w) > 3)
            if words:
                for item in registry:
                    item_desc = re.sub(r'\s+', ' ', item['description'].strip().lower())
                    item_words = set(w for w in item_desc.split() if len(w) > 3)
                    if words == item_words or (len(words & item_words) / len(words)) >= 0.85:
                        best_match = item
                        break
                        
        if best_match:
            script_dir = Path.home() / "safe_scripts"
            filepath = script_dir / best_match['filename']
            if filepath.exists():
                try:
                    code_content = filepath.read_text()
                except Exception:
                    code_content = ""
                return (
                    f"✅ **Script Ditemukan (Reused)**\n"
                    f"Permintaan Anda mirip dengan script yang sudah dibuat sebelumnya.\n\n"
                    f"📁 **File:** `{filepath}`\n"
                    f"📝 **Deskripsi Terdaftar:** {best_match['description']}\n\n"
                    f"**Isi Script:**\n```\n{code_content}\n```\n"
                    f"Cara pakai: Jalankan `{filepath}` di terminal."
                )

        existing_context = ""
        if registry:
            existing_context = "\nBerikut adalah daftar script yang SUDAH pernah dibuat sebelumnya:\n"
            for item in registry:
                existing_context += f"- File: {item['filename']} | Deskripsi: {item['description']}\n"
            existing_context += (
                "\nJika permintaan user di atas memiliki maksud/tujuan yang sama atau sangat mirip dengan script yang sudah ada, "
                "JANGAN membuat script baru. Cukup jelaskan secara singkat dan informasikan cara menjalankan script yang sudah ada tersebut "
                "tanpa menulis block kode baru.\n"
            )
            
        system = (
            "Kamu adalah ahli automation Linux. Hasilkan script bash atau python yang aman dan siap pakai.\n"
            "Gunakan path dinamis (seperti $HOME) atau path relatif, bukan path hardcoded seperti /home/user.\n"
            "Berikan output script di dalam code block.\n"
            f"{existing_context}"
        )
        prompt = f"Buat script untuk: {description}. Berikan penjelasan cara pakai."
        result = await _call_nim(prompt, system, max_tokens=1200)
        
        script_dir = Path.home() / "safe_scripts"
        script_dir.mkdir(parents=True, exist_ok=True)
        
        if "```" in result:
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            code = result
            ext = "sh"
            match = re.search(r"```(?:bash|sh|python|py)?\s*(.*?)\s*```", result, re.DOTALL)
            if match:
                code = match.group(1).strip()
                if "import " in code or "def " in code or "print(" in code:
                    ext = "py"
            
            filepath = script_dir / f"auto_{ts}.{ext}"
            with open(filepath, "w") as f:
                if ext == "sh" and not code.startswith("#!"):
                    f.write(f"#!/bin/bash\n# Auto-generated: {description}\n# {datetime.now().isoformat()}\n\n{code}\n")
                else:
                    f.write(code + "\n")
            os.chmod(filepath, 0o755)
            
            registry.append({
                "filename": filepath.name,
                "description": description,
                "created_at": datetime.now().isoformat()
            })
            _save_registry(registry)
            
            return f"✅ Script automation dibuat:\n\n{result}\n\n📁 {filepath}"
        else:
            return f"✅ Reused Script:\n\n{result}"
    except NIMCallError as e:
        return str(e)

async def ai_summarize(target: str) -> str:
    target_path = Path(target).expanduser()
    if not target_path.exists():
        return f"❌ Target tidak ditemukan: {target}"
    content = ""
    if target_path.is_file():
        try:
            content = target_path.read_text(errors="ignore")[:3000]
        except Exception as e:
            return f"❌ Gagal membaca file: {e}"
    elif target_path.is_dir():
        files = list(target_path.iterdir())[:20]
        for f in files:
            content += f"{f.name} ({f.stat().st_size if f.is_file() else 'dir'})\n"
    if not content.strip():
        return "❌ Tidak ada konten untuk diringkas."
    
    try:
        system = "Ringkas konten berikut dalam Bahasa Indonesia. Berikan poin-poin penting."
        result = await _call_nim(f"Ringkas:\n{content}", system, max_tokens=600)
        AI_WORK_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = AI_WORK_DIR / f"ringkasan_{ts}.md"
        with open(filepath, "w") as f:
            f.write(f"# Ringkasan: {target}\n\nDate: {datetime.now().isoformat()}\n\n{result}\n")
        return f"📝 Ringkasan:\n\n{result}\n\n📁 {filepath}"
    except NIMCallError as e:
        return str(e)

async def ai_research(topic: str, depth: str = "medium") -> str:
    try:
        system = "Kamu adalah asisten riset. Berikan informasi mendalam, terstruktur, dengan sumber."
        prompt = f"Lakukan riset {depth} tentang: {topic}. Berikan: 1) Ringkasan 2) Poin utama 3) Referensi"
        result = await _call_nim(prompt, system, max_tokens=1200)
        AI_RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in " _-")[:30] or "riset"
        filepath = AI_RESEARCH_DIR / f"{ts}_{safe_topic.replace(' ', '_')}.md"
        with open(filepath, "w") as f:
            f.write(f"# Riset: {topic}\nDepth: {depth}\nDate: {datetime.now().isoformat()}\n\n{result}\n")
        return f"🔬 Hasil Riset ({depth}):\n\n{result}\n\n📁 {filepath}"
    except NIMCallError as e:
        return str(e)

async def ai_insight(period: str = "daily") -> str:
    import psutil
    now = datetime.now()
    if period == "weekly":
        start = now - timedelta(days=7)
    elif period == "monthly":
        start = now - timedelta(days=30)
    else:
        start = now - timedelta(days=1)
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime = now - boot
    system_data = f"Sistem: CPU={cpu}%, RAM={ram.percent}%, Disk={disk.percent}%, Uptime={uptime.days} hari {uptime.seconds//3600} jam, Boot={boot.strftime('%H:%M')}"
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            if p.info["cpu_percent"] and p.info["cpu_percent"] > 1:
                procs.append(p.info)
        except Exception:
            pass
    procs = sorted(procs, key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)[:5]
    if procs:
        system_data += "\nTop Proses:\n" + "\n".join(f"  {p['name']}: CPU {p.get('cpu_percent', 0):.1f}%" for p in procs)
    
    try:
        system = "Analisis data sistem dan berikan insight serta rekomendasi dalam Bahasa Indonesia."
        prompt = f"Periode: {period}. Data:\n{system_data}\n\nBerikan insight dan saran perbaikan."
        result = await _call_nim(prompt, system, max_tokens=600)
        AI_WORK_DIR.mkdir(parents=True, exist_ok=True)
        ts = now.strftime("%Y%m%d_%H%M")
        filepath = AI_WORK_DIR / f"insight_{period}_{ts}.md"
        with open(filepath, "w") as f:
            f.write(f"# AI Insight ({period})\n\nDate: {now.isoformat()}\n\n{system_data}\n\n## Analisis\n\n{result}\n")
        return f"🧠 Insight {period}:\n\n{result}\n\n📁 {filepath}"
    except NIMCallError as e:
        return str(e)
