"""
Advanced Problem Solver with live web access and memory cache.
"""
import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

SOLVER_PROMPT = """Kamu adalah problem solver expert. User punya masalah berikut:

PROBLEM: {problem}

Hasil pencarian web terkait:
{web_results}

Tugasmu:
1. Analisis masalah berdasarkan konteks yang diberikan
2. Berikan 3-5 langkah solusi yang konkret dan actionable
3. Prioritaskan solusi yang paling mungkin berhasil
4. Sertakan command/code jika relevan (dalam code block)
5. Jika ada risiko, beri peringatan
6. Gunakan bahasa Indonesia

Format response:
🔍 **Analisis:** [analisis singkat masalah]
📋 **Solusi:**
1. [langkah 1]
2. [langkah 2]
...
⚠️ **Peringatan:** [jika ada]
"""


class SolverEngine:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get(
            "NVIDIA_NIM_BASE_URL",
            "https://integrate.api.nvidia.com/v1",
        )

    async def solve(self, problem: str) -> str:
        try:
            cached = memory_manager.search(problem, k=3)
            for c in cached:
                if c.get("distance", 1) < 0.15:
                    ts = c["metadata"].get("timestamp", "")[:10]
                    return (
                        f"📦 *Solusi dari memory (cache {ts}):*\n\n"
                        f"{c['text']}"
                    )
        except Exception:
            pass

        web_results = await self._search_web(problem)
        result = await self._call_solver_nim(problem, web_results)

        try:
            memory_manager.remember(
                f"Solved problem: {problem}\nSolution: {result[:500]}",
                source="solver",
                topic="solved_problems",
                tags=["problem_solved", "solver"],
            )
        except Exception:
            pass

        return result

    async def _search_web(self, query: str) -> str:
        try:
            from agent.scraper import smart_search
            results = await smart_search(query, max_results=3, use_ai=False)
            return results[:2000]
        except Exception:
            return "Web search unavailable."

    async def _call_solver_nim(self, problem: str, web_results: str) -> str:
        prompt = SOLVER_PROMPT.format(problem=problem, web_results=web_results[:2000])
        if not self.nim_api_key:
            return "❌ NIM API key belum di-set. Set env NVIDIA_NIM_API_KEY untuk menggunakan fitur ini."
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.nim_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1024,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
        except httpx.TimeoutException:
            return "⏱️ AI solver timeout. Coba lagi nanti."
        except Exception:
            return "❌ Gagal memproses solusi. Periksa koneksi dan API key."


solver = SolverEngine()
