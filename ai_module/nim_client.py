"""
NVIDIA NIM AI Interpreter
Menerjemahkan natural language → perintah sistem yang valid dan aman
Memiliki fallback logic jika API tidak tersedia
"""
import os
import re
import json
import asyncio
import httpx
import platform
from typing import Optional
from loguru import logger
from .fallback_parser import FallbackParser
from .prompt_templates import SYSTEM_PROMPT

NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
NIM_BASE_URL = os.environ.get(
    "NVIDIA_NIM_BASE_URL",
    "https://integrate.api.nvidia.com/v1"
)
NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")
AI_ENABLED = os.environ.get("AI_MODE_ENABLED", "true").lower() == "true"

# Timeout untuk API call (LLM might be slow)
API_TIMEOUT = 30.0

class NIMClient:

    def __init__(self):
        self.enabled = AI_ENABLED and bool(NIM_API_KEY)
        self.history = [] # Memori chat: [{"role": "...", "content": "..."}]
        self.current_os = platform.system()
        if not NIM_API_KEY and AI_ENABLED:
            logger.warning("AI mode enabled tapi NVIDIA_NIM_API_KEY tidak di-set. Fallback ke explicit mode.")

    async def translate_to_command(self, natural_input: str) -> Optional[str]:
        """
        Terjemahkan natural language ke perintah sistem dengan memori.
        """
        if not self.enabled:
            return None

        if natural_input.startswith("!"):
            return None

        try:
            # 1. Update history (User message)
            self.history.append({"role": "user", "content": natural_input[:500]})
            
            # 2. Call API with context
            ai_response = await self._call_nim_api()
            
            if ai_response:
                # 3. Update history (Assistant response)
                self.history.append({"role": "assistant", "content": ai_response})
                
                # 4. Sliding window: simpan hanya 10 pesan terakhir (5 turns)
                if len(self.history) > 10:
                    self.history = self.history[-10:]
                    
            return ai_response
        except Exception as e:
            logger.error(f"NIM contextual error: {e}")
            return None

    async def _call_nim_api(self) -> Optional[str]:
        """Panggil NVIDIA NIM API dengan konteks history dan OS awareness."""
        headers = {
            "Authorization": f"Bearer {NIM_API_KEY}",
            "Content-Type": "application/json",
        }

        # Inject current OS into prompt
        formatted_prompt = SYSTEM_PROMPT.format(current_os=self.current_os)

        # Gunakan history + formatted system prompt
        messages = [{"role": "system", "content": formatted_prompt}] + self.history

        payload = {
            "model": NIM_MODEL,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.post(
                f"{NIM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        raw_output = data["choices"][0]["message"]["content"].strip()
        
        # Parse JSON response
        try:
            parsed = json.loads(raw_output)
            command = parsed.get("command", "UNKNOWN")
            reason = parsed.get("reason", "")

            if command in ("UNKNOWN", "BLOCKED", "CHAT"):
                return f"__NIM_{command}__:{reason}"

            if not self._validate_ai_output(command):
                return None

            return command
        except:
            return None

    def _validate_ai_output(self, command: str) -> bool:
        """Validasi output AI untuk fitur terbaru."""
        valid_commands = {
            "!screenshot", "!sysinfo", "!lock", "!reboot", "!term", "!exit", "!help", "!video", "!webcam", "!webcamvid"
        }
        valid_prefixes = ("!ls ", "!get ", "!run ", "!video ", "!cd ", "!gemini ", "!opencode ", "!antigravity ")

        if command in valid_commands:
            return True

        if any(command.startswith(p) for p in valid_prefixes):
            # Cek argumen berbahaya
            arg = command.split(" ", 1)[1] if " " in command else ""
            dangerous_chars = set(";&|`$\x00")
            return not any(c in arg for c in dangerous_chars)

        return False


class CommandInterpreter:
    """
    Orchestrator utama: coba NIM dulu, fallback ke explicit parser.
    """

    def __init__(self):
        self.nim = NIMClient()
        self.fallback = FallbackParser()

    async def interpret(self, user_input: str) -> tuple[Optional[str], list[str]]:
        """
        Interpretasikan input user.
        Return (command_name, args)
        """
        # Coba AI translation dulu
        ai_result = await self.nim.translate_to_command(user_input)

        if ai_result is not None:
            # AI berhasil translate
            if ai_result.startswith("__NIM_"):
                # AI merespons dengan CHAT, BLOCKED, atau UNKNOWN
                return None, [ai_result]
            # Parse hasil AI seperti explicit command
            return self.fallback.parse(ai_result)

        # Fallback ke explicit parser
        logger.debug(f"Using fallback parser for: {user_input}")
        return self.fallback.parse(user_input)
