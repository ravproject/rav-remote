import os
import json
import asyncio
import httpx
from loguru import logger
from agent.memory.manager import memory_manager


RESEARCH_SYSTEM_PROMPT = """Kamu adalah researcher AI yang membuat laporan riset.
Topik: {topic}
Depth: {depth}

Data yang terkumpul:
{data}

Tugasmu:
1. Buat laporan riset yang terstruktur
2. Sertakan poin-poin utama, data pendukung, dan sumber
3. Berikan rekomendasi atau kesimpulan di akhir
4. Gunakan bahasa Indonesia

Format:
🔍 *Ringkasan:* [ringkasan 2-3 kalimat]
📋 *Poin Utama:*
• [poin 1]
• [poin 2]
...
📚 *Sumber:*
• [URL 1]
• [URL 2]
...
💡 *Rekomendasi:* [rekomendasi]
"""


class ResearchEngine:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def research(self, topic: str, depth: str = "medium") -> str:
        if not self.nim_api_key:
            return "❌ NIM API key belum di-set."

        depth = depth.lower()
        if depth not in ("light", "medium", "deep"):
            depth = "medium"

        depth_config = {
            "light": {"queries": 1, "results": 5, "label": "Ringan"},
            "medium": {"queries": 2, "results": 8, "label": "Sedang"},
            "deep": {"queries": 3, "results": 10, "label": "Mendalam"},
        }
        cfg = depth_config[depth]

        all_data = []
        from agent.scraper import _search_engines

        for i in range(cfg["queries"]):
            q = topic if i == 0 else f"{topic} {'panduan tutorial review kelebihan kekurangan'.split()[i-1]}"
            try:
                results = await _search_engines(q, max_results=cfg["results"])
                if results:
                    lines = [f"Query: {q}"]
                    for r in results[:cfg["results"]]:
                        lines.append(f"- {r.get('title','')}: {r.get('snippet','')[:300]}")
                        if r.get("url"):
                            lines.append(f"  🔗 {r['url']}")
                    all_data.append("\n".join(lines))
            except Exception:
                pass
            await asyncio.sleep(0.3)

        combined_data = "\n\n---\n\n".join(all_data) if all_data else "Tidak ada data terkumpul."

        prompt = RESEARCH_SYSTEM_PROMPT.format(
            topic=topic,
            depth=cfg["label"],
            data=combined_data[:3000],
        )

        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "system", "content": prompt}],
                        "max_tokens": 1536,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                report = resp.json()["choices"][0]["message"]["content"].strip()

            try:
                async with asyncio.timeout(5):
                    memory_manager.remember(
                        f"Research ({depth}): {topic}\n\n{report[:500]}",
                        source="research",
                        topic="research",
                        tags=["research", depth, topic[:30]],
                    )
            except Exception:
                pass

            return f"📚 *Laporan Riset: {topic}* ({cfg['label']})\n\n{report}"
        except httpx.TimeoutException:
            return "⏱️ Riset timeout. Coba depth yang lebih ringan."
        except Exception as e:
            logger.error(f"Research error: {e}")
            return "❌ Gagal melakukan riset."


research_engine = ResearchEngine()
