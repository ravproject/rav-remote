
import os
import time
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY")
NIM_BASE_URL = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")

from ai_module.prompt_templates import SYSTEM_PROMPT

async def test_ai_latency(user_input):
    headers = {
        "Authorization": f"Bearer {NIM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": NIM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        "max_tokens": 100,
        "temperature": 0.1,
    }

    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{NIM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            end_time = time.time()
            return end_time - start_time, response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return None, str(e)

async def main():
    print(f"Testing latency for: 'apa saja yang bisa kamu lakukan?'")
    latency, result = await test_ai_latency("apa saja yang bisa kamu lakukan?")
    if latency:
        print(f"Latency: {latency:.2f} seconds")
        print(f"Result: {result}")
    else:
        print(f"Error: {result}")

if __name__ == "__main__":
    asyncio.run(main())
