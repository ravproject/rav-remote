
import os
import asyncio
import httpx
from dotenv import load_dotenv
from ai_module.prompt_templates import SYSTEM_PROMPT

load_dotenv()

NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY")
NIM_BASE_URL = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")

async def interpret(user_input):
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

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{NIM_BASE_URL}/chat/completions", headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"]

async def debug_cases():
    cases = ["kamu siapa sih sebenarnya?", "rekam dong 10 detik"]
    for case in cases:
        print(f"CASE: {case}")
        res = await interpret(case)
        print(f"RAW OUTPUT: {res}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(debug_cases())
