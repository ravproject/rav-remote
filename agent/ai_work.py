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
NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")

async def _call_nim(prompt: str, system_prompt: str = None, max_tokens: int = 500) -> str:
    if not NIM_API_KEY:
        return "AI tidak tersedia: NVIDIA_NIM_API_KEY tidak di-set."
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
    except Exception as e:
        return f"Gagal memanggil AI: {e}"

async def ai_work(task: str) -> str:
    AI_WORK_DIR.mkdir(parents=True, exist_ok=True)
    system = "Kamu adalah asisten produktivitas. Jawab dengan ringkas dan actionable."
    result = await _call_nim(task, system, max_tokens=800)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = AI_WORK_DIR / f"ai_work_{ts}.md"
    with open(filepath, "w") as f:
        f.write(f"# AI Work: {task}\n\nDate: {datetime.now().isoformat()}\n\n{result}\n")
    return f"✅ {result}\n\n📁 Disimpan: {filepath}"

async def ai_write(doc_type: str, topic: str) -> str:
    AI_WORK_DIR.mkdir(parents=True, exist_ok=True)
    system = f"Kamu adalah asisten menulis. Buatkan {doc_type} profesional dalam Bahasa Indonesia."
    prompt = f"Buatkan {doc_type} tentang: {topic}"
    result = await _call_nim(prompt, system, max_tokens=1000)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    safe_type = "".join(c for c in doc_type if c.isalnum() or c in " _-") or "dokumen"
    filepath = AI_WORK_DIR / f"{ts}_{safe_type}_{topic[:20].replace(' ', '_')}.md"
    with open(filepath, "w") as f:
        f.write(f"# {doc_type}: {topic}\n\nDate: {datetime.now().isoformat()}\n\n{result}\n")
    return f"✅ Draft {doc_type} selesai:\n\n{result[:500]}\n\n📁 {filepath}"

async def ai_automate(description: str) -> str:
    script_dir = Path.home() / "safe_scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    system = "Kamu adalah ahli automation Linux. Hasilkan script bash/python yang aman dan siap pakai. Berikan output dalam format code block."
    prompt = f"Buat script untuk: {description}. Berikan penjelasan cara pakai."
    result = await _call_nim(prompt, system, max_tokens=1200)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = script_dir / f"auto_{ts}.sh"
    with open(filepath, "w") as f:
        f.write(f"#!/bin/bash\n# Auto-generated: {description}\n# {datetime.now().isoformat()}\n\n{result}\n")
    os.chmod(filepath, 0o755)
    return f"✅ Script automation dibuat:\n\n{result[:500]}\n\n📁 {filepath}"

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
    system = "Ringkas konten berikut dalam Bahasa Indonesia. Berikan poin-poin penting."
    result = await _call_nim(f"Ringkas:\n{content}", system, max_tokens=600)
    AI_WORK_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = AI_WORK_DIR / f"ringkasan_{ts}.md"
    with open(filepath, "w") as f:
        f.write(f"# Ringkasan: {target}\n\nDate: {datetime.now().isoformat()}\n\n{result}\n")
    return f"📝 Ringkasan:\n\n{result}\n\n📁 {filepath}"

async def ai_research(topic: str, depth: str = "medium") -> str:
    AI_RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    system = "Kamu adalah asisten riset. Berikan informasi mendalam, terstruktur, dengan sumber."
    prompt = f"Lakukan riset {depth} tentang: {topic}. Berikan: 1) Ringkasan 2) Poin utama 3) Referensi"
    result = await _call_nim(prompt, system, max_tokens=1200)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    safe_topic = "".join(c for c in topic if c.isalnum() or c in " _-")[:30] or "riset"
    filepath = AI_RESEARCH_DIR / f"{ts}_{safe_topic.replace(' ', '_')}.md"
    with open(filepath, "w") as f:
        f.write(f"# Riset: {topic}\nDepth: {depth}\nDate: {datetime.now().isoformat()}\n\n{result}\n")
    return f"🔬 Hasil Riset ({depth}):\n\n{result[:800]}\n\n📁 {filepath}"

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
    system_data = f"Sistem: CPU={cpu}%, RAM={ram.percent}%, Disk={disk.percent}%, Uptime={uptime.days}h {uptime.seconds//3600}j, Boot={boot.strftime('%H:%M')}"
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
    system = "Analisis data sistem dan berikan insight serta rekomendasi dalam Bahasa Indonesia."
    prompt = f"Periode: {period}. Data:\n{system_data}\n\nBerikan insight dan saran perbaikan."
    result = await _call_nim(prompt, system, max_tokens=600)
    AI_WORK_DIR.mkdir(parents=True, exist_ok=True)
    ts = now.strftime("%Y%m%d_%H%M")
    filepath = AI_WORK_DIR / f"insight_{period}_{ts}.md"
    with open(filepath, "w") as f:
        f.write(f"# AI Insight ({period})\n\nDate: {now.isoformat()}\n\n{system_data}\n\n## Analisis\n\n{result}\n")
    return f"🧠 Insight {period}:\n\n{result}\n\n📁 {filepath}"
