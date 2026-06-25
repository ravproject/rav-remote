import os
import json
import asyncio
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

EXPLAIN_PROMPT = """Kamu adalah AI explainer yang membuat konsep kompleks jadi mudah dipahami.
Konsep: {concept}
Level detail: {level}
Konteks: {context}

Tugasmu:
1. Jelaskan konsep "{concept}" dari fundamental sampai advanced
2. Gunakan analogi yang relevan dengan kehidupan sehari-hari
3. Sertakan contoh konkret
4. Akhiri dengan "Next step" — apa yang bisa dipelajari selanjutnya
5. Gunakan bahasa Indonesia

Format:
📖 *Penjelasan: {concept}*

🎯 *Apa itu?*
[definisi sederhana dalam 1-2 kalimat]

🔍 *Penjelasan Detail:*
[penjelasan langkah demi langkah]

💡 *Analogi:*
[analogi yang memudahkan pemahaman]

📝 *Contoh:*
[contoh konkret]

🎓 *Next Step:*
[topik lanjutan yang bisa dipelajari]
"""


class Explainer:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def explain(self, concept: str, level: str = "medium") -> str:
        from agent.scraper import _search_engines

        try:
            results = await _search_engines(f"{concept} penjelasan", max_results=4)
            context = ""
            if results:
                snippets = []
                for r in results:
                    title = r.get("title", "")
                    snippet = r.get("snippet", "")
                    if title and snippet:
                        snippets.append(f"- {title}: {snippet[:300]}")
                        if r.get("url"):
                            snippets.append(f"  🔗 {r['url']}")
                context = "\n".join(snippets) if snippets else "Tidak ada konteks dari web."
            else:
                context = "Tidak ada konteks dari web."
        except Exception:
            context = "Pencarian web tidak tersedia."

        level_label = {"basic": "Dasar", "medium": "Menengah", "advanced": "Lanjutan"}.get(level, "Menengah")

        if not self.nim_api_key:
            return f"📖 *{concept}*\n\n{context[:2000]}"

        prompt = EXPLAIN_PROMPT.format(
            concept=concept,
            level=level_label,
            context=context[:3000],
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
                        "temperature": 0.4,
                    },
                )
                resp.raise_for_status()
                result = resp.json()["choices"][0]["message"]["content"].strip()

                try:
                    memory_manager.remember(
                        f"Explain: {concept} ({level})",
                        source="explain",
                        topic="explanation",
                        tags=["explain", concept[:30], level],
                    )
                except Exception:
                    pass

                return result
        except httpx.TimeoutException:
            return f"⏱️ Penjelasan timeout.\n\n📖 *{concept}*\n\n{context[:1500]}"
        except Exception as e:
            logger.error(f"Explainer error: {e}")
            return "❌ Gagal menjelaskan konsep."


explainer = Explainer()
