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

# Timeout untuk API call
API_TIMEOUT = 15.0

class NIMClient:

    def __init__(self):
        self.enabled = AI_ENABLED and bool(NIM_API_KEY)
        if not NIM_API_KEY and AI_ENABLED:
            logger.warning("AI mode enabled tapi NVIDIA_NIM_API_KEY tidak di-set. Fallback ke explicit mode.")

    async def translate_to_command(self, natural_input: str) -> Optional[str]:
        """
        Terjemahkan natural language ke perintah sistem.
        Return None jika harus fallback ke explicit parser.
        """
        if not self.enabled:
            return None  # Signal untuk fallback

        # Cek apakah input sudah berupa explicit command
        if natural_input.startswith("!"):
            return None  # Langsung ke explicit parser

        try:
            return await self._call_nim_api(natural_input)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"NIM API timeout/connection error: {e}. Falling back to explicit mode.")
            return None
        except Exception as e:
            logger.error(f"NIM API unexpected error: {e}. Falling back to explicit mode.")
            return None

    async def _call_nim_api(self, user_input: str) -> Optional[str]:
        """Panggil NVIDIA NIM API."""
        headers = {
            "Authorization": f"Bearer {NIM_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": NIM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input[:500]},  # Batasi input
            ],
            "max_tokens": 100,
            "temperature": 0.1,  # Rendah untuk konsistensi
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
        logger.debug(f"NIM raw output: {raw_output}")

        # Parse JSON response
        try:
            parsed = json.loads(raw_output)
            command = parsed.get("command", "UNKNOWN")
            reason = parsed.get("reason", "")

            if command in ("UNKNOWN", "BLOCKED", "CHAT"):
                logger.info(f"NIM blocked/unknown/chat: {reason}")
                return f"__NIM_{command}__:{reason}"

            # Validasi command yang dihasilkan AI tetap aman
            if not self._validate_ai_output(command):
                logger.warning(f"NIM output failed validation: {command}")
                return None

            logger.info(f"NIM translated '{user_input[:50]}' → '{command}'")
            return command

        except json.JSONDecodeError:
            logger.warning(f"NIM returned non-JSON: {raw_output}")
            return None

    def _validate_ai_output(self, command: str) -> bool:
        """
        VALIDASI KEDUA pada output AI.
        Meskipun AI sudah diberi prompt ketat, selalu validasi lagi.
        """
        valid_commands = {
            "!screenshot", "!sysinfo", "!lock", "!reboot"
        }

        # Perintah dengan argumen
        valid_prefixes = ("!ls ", "!get ", "!run ")

        if command in valid_commands:
            return True

        if any(command.startswith(p) for p in valid_prefixes):
            # Cek argumen tidak mengandung karakter berbahaya
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
