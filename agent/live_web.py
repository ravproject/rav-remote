import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager


_last_context = {}

LIVE_WEB_PROMPT = """Kamu adalah asisten pencarian web live.
Query user: {query}

Hasil pencarian:
{search_results}

Tugasmu:
1. Pilih hasil yang paling relevan dengan query
2. Beri ringkasan singkat untuk setiap hasil
3. Jika user bisa follow-up, tawarkan di akhir
4. Gunakan bahasa Indonesia

Format:
📌 *[judul]* — [ringkasan singkat]
🔗 [URL]

[Jika perlu:] Ada yang ingin ditanyakan lebih lanjut?
"""


class LiveWeb:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def search(self, query: str) -> str:
        global _last_context
        _last_context["query"] = query

        try:
            from agent.scraper import smart_search
            results = await smart_search(query, max_results=5, max_words_per_page=500, use_ai=False)
        except Exception:
            results = "Pencarian web tidak tersedia."

        if not self.nim_api_key:
            return f"🔍 *Hasil Pencarian: {query}*\n\n{results[:2000]}"

        prompt = LIVE_WEB_PROMPT.format(query=query, search_results=results[:3000])

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 800,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"LiveWeb error: {e}")
            return f"🔍 *Hasil Pencarian: {query}*\n\n{results[:1500]}"

    def get_last_context(self) -> dict:
        return _last_context


live_web = LiveWeb()
