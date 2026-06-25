import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

IMAGE_GEN_PROMPT = """Kamu adalah generator prompt gambar AI.
Deskripsi user: {prompt}

Tugasmu:
1. Buat prompt detail dalam Bahasa Inggris untuk image generation
2. Sertakan gaya, komposisi, pencahayaan, warna
3. Berikan juga deskripsi visual dalam Bahasa Indonesia

Format:
🎨 *Prompt Gambar:* {prompt}

🖌️ *Prompt AI (English):*
[prompt detail dalam bahasa Inggris untuk image generation]

📝 *Deskripsi Visual:*
[deskripsi gambar dalam Bahasa Indonesia]
"""


class ImageGenerator:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def generate(self, prompt: str) -> str:
        if not self.nim_api_key:
            return f"❌ NIM API key belum di-set.\n\n📝 *Prompt:* {prompt}\n\nGunakan `!gambar <deskripsi>` untuk generate prompt gambar."

        text_prompt = IMAGE_GEN_PROMPT.format(prompt=prompt)

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [{"role": "user", "content": text_prompt}],
                        "max_tokens": 1024,
                        "temperature": 0.8,
                    },
                )
                resp.raise_for_status()
                result = resp.json()["choices"][0]["message"]["content"].strip()

                try:
                    image_prompt_nim = await self._try_diffusion(prompt)
                    if image_prompt_nim:
                        result += f"\n\n🔄 *Mencoba generate dengan DiffusionGemma...*\n{image_prompt_nim}"
                except Exception:
                    pass

                return result
        except Exception as e:
            logger.error(f"ImageGen error: {e}")
            return f"❌ Gagal generate prompt gambar.\n\n📝 *Prompt:* {prompt}"

    async def _try_diffusion(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "google/diffusiongemma-26b-a4b-it",
                        "messages": [{"role": "user", "content": f"Generate an image: {prompt}"}],
                        "max_tokens": 500,
                    },
                )
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    return content[:1000]
        except Exception:
            pass
        return "⚠️ Image generation via DiffusionGemma tidak tersedia dengan API key ini."


image_generator = ImageGenerator()
