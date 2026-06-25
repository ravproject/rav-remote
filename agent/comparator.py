import os
import json
import asyncio
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

COMPARATOR_PROMPT = """Kamu adalah pembanding AI.
Item A: {item_a}
Item B: {item_b}
Kriteria: {criteria}

Data Item A:
{data_a}

Data Item B:
{data_b}

Tugasmu:
1. Bandingkan kedua item berdasarkan data yang ada
2. Gunakan tabel perbandingan untuk atribut-atribut penting
3. Beri kelebihan dan kekurangan masing-masing
4. Beri rekomendasi berdasarkan kebutuhan berbeda
5. Gunakan bahasa Indonesia

Format:
⚖️ *Perbandingan: {item_a} vs {item_b}*

📊 *Tabel Perbandingan*
| Atribut | {item_a} | {item_b} |
|---------|----------|----------|
| [atribut 1] | [nilai A] | [nilai B] |
| [atribut 2] | [nilai A] | [nilai B] |
...

✅ *Kelebihan {item_a}:*
• [kelebihan]

✅ *Kelebihan {item_b}:*
• [kelebihan]

💡 *Rekomendasi:*
• [rekomendasi berdasarkan kebutuhan]
"""

SINGLE_ITEM_PROMPT = """Kamu adalah pembanding AI.
Item yang dicari: {item}
Kriteria: {criteria}
Data:
{data}

Tugasmu:
1. Analisis item berdasarkan data
2. Buat tabel spesifikasi / fitur
3. Beri kelebihan dan kekurangan
4. Beri rekomendasi
5. Gunakan bahasa Indonesia

Format:
📋 *Analisis: {item}*
📊 *Spesifikasi:*
| Atribut | Nilai |
|---------|-------|
| ... | ... |

✅ *Kelebihan:* ...
❌ *Kekurangan:* ...
💡 *Rekomendasi:* ...
"""


class Comparator:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def compare(self, item_a: str, item_b: str = "", criteria: str = "") -> str:
        from agent.scraper import _search_engines

        async def search_item(item: str) -> str:
            variations = [item, f"{item} spesifikasi", f"{item} review 2026", f"{item} harga"]
            snippets = []
            for q in variations:
                try:
                    results = await _search_engines(q, max_results=3)
                    if results:
                        for r in results[:3]:
                            snippets.append(
                                f"- {r.get('title','')}: {r.get('snippet','')[:250]}"
                            )
                            if r.get("url"):
                                snippets.append(f"  🔗 {r['url']}")
                except Exception:
                    pass
                await asyncio.sleep(0.2)
            return "\n".join(snippets) if snippets else "Tidak ada data."

        data_a = await search_item(item_a)

        if item_b:
            data_b = await search_item(item_b)
            if not criteria:
                criteria = f"Perbandingan antara {item_a} dan {item_b}"

            if not self.nim_api_key:
                return (
                    f"⚖️ *{item_a} vs {item_b}*\n\n"
                    f"📊 *{item_a}:*\n{data_a[:1000]}\n\n"
                    f"📊 *{item_b}:*\n{data_b[:1000]}"
                )

            prompt = COMPARATOR_PROMPT.format(
                item_a=item_a,
                item_b=item_b,
                criteria=criteria,
                data_a=data_a[:3000],
                data_b=data_b[:3000],
            )
        else:
            data_b = ""
            if not criteria:
                criteria = f"Analisis {item_a}"

            if not self.nim_api_key:
                return f"📋 *Analisis: {item_a}*\n\n{data_a[:2000]}"

            prompt = SINGLE_ITEM_PROMPT.format(
                item=item_a,
                criteria=criteria,
                data=data_a[:3500],
            )

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1536,
                        "temperature": 0.2,
                    },
                )
                resp.raise_for_status()
                result = resp.json()["choices"][0]["message"]["content"].strip()

                try:
                    tags = ["comparator", item_a]
                    if item_b:
                        tags.append(item_b)
                    memory_manager.remember(
                        f"Compare: {item_a} vs {item_b}" if item_b else f"Analyze: {item_a}",
                        source="comparator",
                        topic="comparison",
                        tags=tags,
                    )
                except Exception:
                    pass

                return result
        except httpx.TimeoutException:
            return f"⏱️ Perbandingan timeout.\n\n📊 *Data {item_a}:*\n{data_a[:1000]}" + (f"\n\n📊 *Data {item_b}:*\n{data_b[:1000]}" if item_b else "")
        except Exception as e:
            logger.error(f"Comparator error: {e}")
            return "❌ Gagal melakukan perbandingan."


comparator = Comparator()
