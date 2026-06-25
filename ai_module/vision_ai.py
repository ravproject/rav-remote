"""
VisionAI — Screenshot analysis via NVIDIA NIM vision models.
"""
import os
import base64
import io
import httpx
from PIL import Image
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

class VisionAI:
    def __init__(self):
        self.api_key = os.environ.get("NVIDIA_NIM_API_KEY") or ""
        self.base_url = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.model = os.environ.get("VISION_AI_MODEL", "meta/llama-3.2-11b-vision-instruct")
        self.enabled = bool(self.api_key)
        self._warmed_up = False

    async def _warmup(self):
        if self._warmed_up or not self.enabled:
            return
        self._warmed_up = True
        try:
            tiny = Image.new("RGB", (32, 32), color="black")
            buf = io.BytesIO()
            tiny.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": "test"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ]}],
                "max_tokens": 10,
            }
            async with httpx.AsyncClient(timeout=120.0) as cl:
                await cl.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            logger.info("VisionAI model warmed up")
        except Exception as e:
            logger.debug(f"VisionAI warmup failed (non-critical): {e}")

    async def describe(self, image_bytes: bytes, prompt: str = "") -> str | None:
        if not self.enabled:
            return None

        # Resize image to reduce payload (max 480px wide)
        img = Image.open(io.BytesIO(image_bytes))
        max_w = 480
        if img.width > max_w:
            ratio = max_w / img.width
            img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64}"

        system = (
            "Kamu adalah asisten analisis screenshot. "
            "Deskripsikan apa yang terlihat di screenshot ini secara detail dan informatif. "
            "Sebutkan elemen-elemen visual yang terlihat seperti jendela aplikasi, isi halaman, "
            "icon, tombol, teks yang terbaca, dan tata letak secara umum. "
            "Gunakan bahasa Indonesia yang natural. Langsung ke deskripsi tanpa kata pengantar. "
            "Maksimal 3-4 kalimat."
        )
        if prompt:
            system += f"\nInstruksi tambahan: {prompt}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Apa yang ada di screenshot ini?"},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                },
            ],
            "max_tokens": 500,
            "temperature": 0.3,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as cl:
                r = await cl.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                r.raise_for_status()
                text = r.json()["choices"][0]["message"]["content"].strip()
                return text
        except Exception as e:
            logger.warning(f"VisionAI call failed: {e}")
            return None

vision_ai = VisionAI()
