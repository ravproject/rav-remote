import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager


FACT_CHECK_PROMPT = """Kamu adalah fact-checker AI.
Klaim: {claim}

Bukti dari internet:
{evidence}

Tugasmu:
1. Analisis klaim berdasarkan bukti yang ada
2. Beri rating kepercayaan dalam bentuk persentase (0-100%)
3. Jelaskan alasan rating tersebut
4. Sebutkan sumber yang mendukung atau menyanggah
5. Gunakan bahasa Indonesia

Format:
🔍 *Klaim:* {claim}
✅ *Rating Kepercayaan:* [0-100]%
📝 *Analisis:* [penjelasan detail]
📚 *Sumber:*
• [URL 1] — [keterangan]
• [URL 2] — [keterangan]
"""


class FactChecker:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def verify(self, claim: str) -> str:
        if not self.nim_api_key:
            return "❌ NIM API key belum di-set."

        try:
            from agent.scraper import smart_search
            evidence = await smart_search(claim, max_results=5, max_words_per_page=1500, use_ai=False)
        except Exception:
            evidence = "Pencarian web tidak tersedia."

        if not evidence or len(evidence) < 50:
            return (
                f"⚠️ *Verifikasi Fakta*\n\n"
                f"Klaim: {claim}\n\n"
                f"Tidak cukup bukti ditemukan di internet untuk memverifikasi klaim ini. "
                f"Coba gunakan kata kunci yang lebih spesifik."
            )

        prompt = FACT_CHECK_PROMPT.format(claim=claim, evidence=evidence[:4000])

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
                result = resp.json()["choices"][0]["message"]["content"].strip()

                try:
                    memory_manager.remember(
                        f"Fact check: '{claim}' -> {result[:300]}",
                        source="fact_checker",
                        topic="fact_check",
                        tags=["fact_check", "verification"],
                    )
                except Exception:
                    pass

                return result
        except Exception as e:
            logger.error(f"FactChecker error: {e}")
            return "❌ Gagal memverifikasi fakta."


fact_checker = FactChecker()
