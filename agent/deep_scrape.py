import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager


DEEP_SCRAPE_PROMPT = """Kamu adalah analis web mendalam.
URL: {url}

Konten halaman:
{content}

Tugas user: {task}

Tugasmu:
1. Analisis konten sesuai tugas yang diminta
2. Ekstrak informasi spesifik jika diminta
3. Berikan ringkasan jika diminta
4. Gunakan bahasa Indonesia

Format:
**Analisis:** [hasil analisis sesuai task]
**Detail:** [poin-poin penting]
"""


class DeepScraper:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def analyze(self, url: str, task: str = "") -> str:
        try:
            from agent.scraper import scrape_url
            result = await scrape_url(url, force=False, use_ai=False)
            content = result.get("content", "") or result.get("text", str(result))
        except Exception as e:
            return f"❌ Gagal mengambil konten dari {url}: {e}"

        if not content or len(content) < 50:
            return f"❌ Konten terlalu pendek atau tidak terbaca dari {url}"

        if not task:
            task = "Buat ringkasan dari halaman ini"

        if not self.nim_api_key:
            return f"📄 *Konten dari {url}*\n\n{content[:2000]}"

        prompt = DEEP_SCRAPE_PROMPT.format(url=url, content=content[:5000], task=task)

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1024,
                        "temperature": 0.2,
                    },
                )
                resp.raise_for_status()
                analysis = resp.json()["choices"][0]["message"]["content"].strip()

                try:
                    memory_manager.remember(
                        f"Deep scrape {url}: {analysis[:300]}",
                        source="deep_scrape",
                        topic="deep_scrape",
                        tags=["deep_scrape", "web"],
                    )
                except Exception:
                    pass

                return analysis
        except Exception as e:
            logger.error(f"DeepScrape error: {e}")
            return f"❌ Gagal menganalisis {url}."


deep_scraper = DeepScraper()
