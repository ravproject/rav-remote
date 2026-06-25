import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

TRANSLATE_PROMPT = """Kamu adalah penerjemah AI yang cerdas.
Teks: {text}
Bahasa sumber: {source_lang}
Bahasa target: {target_lang}

Tugasmu:
1. Terjemahkan teks dari {source_lang} ke {target_lang}
2. Pertahankan nada, gaya, dan format asli
3. Jika ada idiom, cari padanan yang natural di bahasa target
4. Sertakan catatan terjemahan jika ada istilah khusus
5. Berikan alternatif jika ada beberapa cara menerjemahkan

Format:
🌐 *Terjemahan: {source_lang} → {target_lang}*

📝 *Hasil:*
[teks terjemahan]

📌 *Catatan:*
• [catatan terjemahan jika ada]
"""

DETECT_PROMPT = """Teks: {text}
Tugas: Deteksi bahasa dari teks di atas.
Output hanya nama bahasa dalam Bahasa Indonesia (contoh: Inggris, Indonesia, Jepang, Arab, dll).
"""


class Translator:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def translate(self, text: str, target_lang: str = "Indonesia", source_lang: str = "") -> str:
        if not text.strip():
            return "❌ Masukkan teks yang akan diterjemahkan."
        if not source_lang:
            source_lang = await self._detect_lang(text)

        if not self.nim_api_key:
            return f"🌐 *Deteksi:* {source_lang}\n📝 *Teks:* {text[:2000]}"

        prompt = TRANSLATE_PROMPT.format(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
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
                        "temperature": 0.1,
                    },
                )
                resp.raise_for_status()
                result = resp.json()["choices"][0]["message"]["content"].strip()

                try:
                    memory_manager.remember(
                        f"Translate: {source_lang} → {target_lang}: {text[:100]}",
                        source="translate",
                        topic="translation",
                        tags=["translate", source_lang, target_lang],
                    )
                except Exception:
                    pass

                return result
        except Exception as e:
            logger.error(f"Translate error: {e}")
            return f"❌ Gagal menerjemahkan.\n\n📝 *Teks asli:* {text[:1000]}"

    async def _detect_lang(self, text: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": DETECT_PROMPT.format(text=text[:500])}],
                        "max_tokens": 20,
                        "temperature": 0,
                    },
                )
                if resp.status_code == 200:
                    lang = resp.json()["choices"][0]["message"]["content"].strip()
                    return lang if lang else "Tidak diketahui"
        except Exception:
            pass
        return "Tidak diketahui"


translator = Translator()
