import os
import json
import asyncio
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

TREND_PROMPT = """Kamu adalah pemburu tren AI.
Topik: {topic}
Data dari internet:
{data}

Tugasmu:
1. Identifikasi tren, pola, atau pergeseran dari data
2. Beri 3-5 tren spesifik dengan bukti pendukung
3. Urutkan dari yang paling signifikan
4. Sertakan sumber untuk setiap tren
5. Gunakan bahasa Indonesia

Format:
🔥 *Tren: {topic}*
Tren #1: **[judul tren]**
  [penjelasan tren]
  📊 Bukti: [data/sumber]
---
💡 *Kesimpulan:* [prediksi arah tren]
"""


class TrendHunter:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def hunt(self, topic: str, days: int = 30) -> str:
        from agent.scraper import _search_engines

        variations = [
            f"{topic} trend 2026",
            f"{topic} terbaru",
            f"{topic} tren berkembang",
            f"{topic} prediksi",
            f"{topic} masa depan",
        ]

        all_data = []
        for q in variations:
            try:
                results = await _search_engines(q, max_results=4)
                if results:
                    lines = [f"Query: {q}"]
                    for r in results[:4]:
                        lines.append(f"- {r.get('title','')}: {r.get('snippet','')[:250]}")
                        if r.get("url"):
                            lines.append(f"  🔗 {r['url']}")
                    all_data.append("\n".join(lines))
            except Exception:
                pass
            await asyncio.sleep(0.3)

        combined = "\n\n---\n\n".join(all_data) if all_data else "Tidak ada data terkumpul."

        if not self.nim_api_key:
            return f"📊 *Tren: {topic}*\n\n{combined[:2500]}"

        prompt = TREND_PROMPT.format(topic=topic, data=combined[:5000])

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1536,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                result = resp.json()["choices"][0]["message"]["content"].strip()

                try:
                    memory_manager.remember(
                        f"Trend: {topic} ({days} days)",
                        source="trend_hunter",
                        topic="trend",
                        tags=["trend", topic],
                    )
                except Exception:
                    pass

                return result
        except httpx.TimeoutException:
            return f"⏱️ Pencarian trend timeout. Coba topik yang lebih spesifik.\n\n📊 *Data mentah:*\n{combined[:1500]}"
        except Exception as e:
            logger.error(f"TrendHunter error: {e}")
            return f"⚠️ Gagal mengidentifikasi trend.\n\n📊 *Data mentah:*\n{combined[:1500]}"


trend_hunter = TrendHunter()
