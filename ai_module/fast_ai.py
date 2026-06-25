"""
FastAI — Ringan, cepat, untuk summarization & processing.
Support OpenAI-compatible API. Load .env otomatis.
"""
import os
import json
import httpx
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def _get_key() -> str:
    k = os.environ.get("FAST_AI_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY") or ""
    return k

def _get_base() -> str:
    return os.environ.get("FAST_AI_BASE_URL") or os.environ.get("NVIDIA_NIM_BASE_URL") or "https://integrate.api.nvidia.com/v1"

def _get_model() -> str:
    return os.environ.get("FAST_AI_MODEL") or os.environ.get("NVIDIA_NIM_MODEL") or "meta/llama-3.1-8b-instruct"

class FastAI:
    def __init__(self):
        self.api_key = _get_key()
        self.base_url = _get_base()
        self.model = _get_model()
        self.fallback_model = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-8b-instruct")
        self.enabled = bool(self.api_key)

    async def summarize(self, text: str, query: str = "") -> str | None:
        if not self.enabled or not text.strip():
            return None

        prompt = (
            "Kamu adalah asisten peringkas informasi. "
            "Ringkas teks berikut dalam 3-5 poin penting, bahasa Indonesia yang natural dan to the point. "
            "Langsung ke intinya, tanpa kata pengantar seperti 'Berikut ringkasannya'. "
            "Gunakan emoji secukupnya."
        )
        if query:
            prompt += f"\nKonteks: {query}"

        # Coba model cepat dulu
        result = await self._call(self.model, prompt, text[:2500])
        if result:
            return result

        # Fallback ke model utama (lebih lambat tapi pasti jalan)
        logger.info(f"FastAI fallback ke model: {self.fallback_model}")
        result = await self._call(self.fallback_model, prompt, text[:2500])
        return result

    async def _call(self, model: str, system: str, user: str) -> str | None:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 400,
            "temperature": 0.3,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as cl:
                r = await cl.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.debug(f"FastAI call failed ({model}): {e}")
            return None

fast_ai = FastAI()
