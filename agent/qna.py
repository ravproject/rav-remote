import os
import json
import asyncio
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

QNA_PROMPT = """Kamu adalah AI Q&A dengan akses internet dan memory.
Pertanyaan: {query}

Konteks dari memory:
{memory_context}

Hasil pencarian web:
{web_results}

Tugasmu:
1. Jawab pertanyaan secara komprehensif berdasarkan semua sumber
2. Jika ada informasi di memory, prioritaskan konteks lokal
3. Sertakan kutipan dan sumber dari web
4. Jika tidak yakin, akui keterbatasan
5. Gunakan bahasa Indonesia

Format:
**Jawaban:** [jawaban lengkap dengan penjelasan]
**Sumber:**
• [judul] — [URL]
💡 **Tahu gak?** [fakta menarik terkait]
"""


class QnAEngine:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def answer(self, query: str) -> str:
        from agent.scraper import _search_engines

        try:
            memory_results = memory_manager.search(query, n_results=3)
            memory_context = ""
            if memory_results and len(memory_results.get("documents", [])) > 0:
                docs = memory_results["documents"]
                memory_context = "\n".join(f"- {d[:300]}" for d in docs if d)
            if not memory_context:
                memory_context = "Tidak ada konteks dari memory."
        except Exception:
            memory_context = "Memory tidak tersedia."

        try:
            results = await _search_engines(query, max_results=6)
            web_results = ""
            if results:
                lines = [f"🔍 Hasil pencarian: {query}"]
                for r in results:
                    lines.append(f"- {r.get('title','')}: {r.get('snippet','')[:300]}")
                    if r.get("url"):
                        lines.append(f"  🔗 {r['url']}")
                web_results = "\n".join(lines)
            else:
                web_results = "Tidak ada hasil pencarian web."
        except Exception:
            web_results = "Pencarian web tidak tersedia."

        if not self.nim_api_key:
            combined = f"Memory: {memory_context[:500]}\n\nWeb: {web_results[:1500]}"
            return f"📚 *Q&A: {query}*\n\n{combined}"

        prompt = QNA_PROMPT.format(
            query=query,
            memory_context=memory_context,
            web_results=web_results[:4000],
        )

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
                        f"Q&A: {query}\nJawaban: {answer[:300]}",
                        source="qna",
                        topic="qna",
                        tags=["qna", query[:30]],
                    )
                except Exception:
                    pass

                return answer
        except httpx.TimeoutException:
            return f"⏱️ Q&A timeout.\n\n📚 *Konteks:*\n{memory_context[:500]}\n\n🌐 *Web:*\n{web_results[:1000]}"
        except Exception as e:
            logger.error(f"QnA error: {e}")
            return "❌ Gagal memproses pertanyaan."


qna_engine = QnAEngine()
