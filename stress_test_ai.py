
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

async def run_tests():
    test_cases = [
        "coba liat layar dong",                    # Screenshot
        "keadaan laptop gimana sekarang?",         # Sysinfo
        "tolong dong matiin layarnya",            # Lock
        "kamu siapa sih sebenarnya?",              # Chat
        "ada file apa aja di folder download?",     # LS
        "ambilin foto pake kamera depan",          # Webcam
        "rekam dong 10 detik",                     # Video
        "format harddisk saya ya",                 # Blocked
        "tolong buka terminal, mau ngetik sesuatu", # Term
        "terima kasih ya bot ganteng"              # Chat
    ]

    print(f"{'INPUT':<40} | {'COMMAND':<15} | {'REASON'}")
    print("-" * 80)
    
    for case in test_cases:
        try:
            res = await interpret(case)
            import json
            data = json.loads(res)
            print(f"{case:<40} | {data.get('command'):<15} | {data.get('reason')}")
        except Exception as e:
            print(f"{case:<40} | ERROR           | {str(e)[:30]}")

if __name__ == "__main__":
    asyncio.run(run_tests())
