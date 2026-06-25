"""
Personal Virtual Companion — Emotional AI assistant with memory context.
"""
import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

COMPANION_PROMPT = """Kamu adalah asisten virtual sekaligus teman yang peduli.
Tugasmu:
1. Ingat semua percakapan sebelumnya dengan user (diberikan sebagai konteks)
2. Pahami perasaan dan mood user
3. Beri dukungan emosional, motivasi, dan saran yang hangat
4. Gunakan bahasa Indonesia yang natural dan ramah
5. Jika user sedang stres/sedih -> beri empati dulu, baru saran
6. Jika user senang -> rayakan bersama
7. Respond in Indonesian unless user speaks English

Gunakan konteks berikut dari memory untuk personalisasi:
{memory_context}

Percakapan terakhir user: {user_input}
"""


class Companion:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get(
            "NVIDIA_NIM_BASE_URL",
            "https://integrate.api.nvidia.com/v1",
        )
        self.model = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")

    async def chat(self, user_input: str, user_id: str) -> str:
        try:
            memory_results = memory_manager.search(user_input, k=5)
            memory_context = "\n".join(
                f"- {r['text'][:200]}" for r in memory_results
            ) if memory_results else "Tidak ada riwayat sebelumnya."
        except Exception:
            memory_context = "Tidak ada riwayat sebelumnya."

        prompt = COMPANION_PROMPT.format(
            memory_context=memory_context,
            user_input=user_input,
        )

        if not self.nim_api_key:
            return "Aku belum punya koneksi AI. Set env NVIDIA_NIM_API_KEY dulu ya! 🤗"

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.nim_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": user_input[:1000]},
                        ],
                        "max_tokens": 512,
                        "temperature": 0.7,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                response = data["choices"][0]["message"]["content"].strip()

                try:
                    memory_manager.remember(
                        f"Companion chat: User said '{user_input[:100]}'. AI replied: '{response[:200]}'",
                        source="companion",
                        topic="personal_chat",
                        tags=["companion", "chat"],
                    )
                except Exception:
                    pass

                return response

        except httpx.TimeoutException:
            return "Maaf, saya agak lambat merespon. Coba ulangi lagi ya? 🙏"
        except Exception as e:
            logger.error(f"Companion error: {e}")
            return "Maaf, aku sedang error. Coba lagi nanti ya. 🤗"


companion = Companion()
