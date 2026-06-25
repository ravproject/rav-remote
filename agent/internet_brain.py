import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager


INTERNET_BRAIN_PROMPT = """Kamu adalah 'Internet Brain' — AI dengan pengetahuan dari internet.
User bertanya: {query}

Hasil pencarian web terkini:
{web_results}

Tugasmu:
1. Jawab pertanyaan user secara komprehensif berdasarkan hasil web
2. Sertakan fakta, data, dan kutipan dari sumber
3. Jika informasi tidak ditemukan, katakan dengan jujur
4. Cantumkan sumber di akhir jawaban
5. Gunakan bahasa Indonesia

Format:
**Jawaban:** [jawaban lengkap]
**Sumber:** [daftar URL sumber]
"""


class InternetBrain:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def answer(self, query: str) -> str:
        if not self.nim_api_key:
            return "❌ NIM API key belum di-set."

        try:
            from agent.scraper import smart_search, _search_engines
            snippets = await _search_engines(query, max_results=8)
            if snippets:
                lines = []
                for s in snippets:
                    lines.append(f"- {s.get('title','')}: {s.get('snippet','')[:300]}")
                    if s.get('url'):
                        lines.append(f"  🔗 {s['url']}")
                web_results = "\n".join(lines)
            else:
                web_results = "Pencarian web tidak tersedia."
        except Exception:
            web_results = "Pencarian web tidak tersedia."

        prompt = INTERNET_BRAIN_PROMPT.format(query=query, web_results=web_results[:4000])

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1024,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                answer = resp.json()["choices"][0]["message"]["content"].strip()

                try:
                    memory_manager.remember(
                        f"Internet Brain Q&A: '{query}' → '{answer[:300]}'",
                        source="internet_brain",
                        topic="internet_brain",
                        tags=["internet_brain", "qa"],
                    )
                except Exception:
                    pass

                return answer
        except httpx.TimeoutException:
            return "⏱️ Internet Brain timeout. Coba lagi nanti."
        except Exception as e:
            logger.error(f"InternetBrain error: {e}")
            return "❌ Gagal mengakses Internet Brain. Periksa koneksi."


internet_brain = InternetBrain()
