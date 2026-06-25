"""
Advanced Autonomous Agent — menerima goal kompleks, membuat rencana,
mengeksekusi sub-tugas secara otonom menggunakan semua fitur existing.
"""
import os
import json
import re
import asyncio
import httpx
from loguru import logger
from bot.command_router import CommandRouter

AUTONOMOUS_PROMPT = """Kamu adalah Autonomous Agent Planner untuk RAV-REMOTE.
User memberikan goal berikut:

GOAL: {goal}

Tugasmu adalah membuat rencana eksekusi dalam bentuk daftar langkah.
Setiap langkah harus menggunakan perintah RAV-REMOTE yang sudah ada.

PERINTAH TERSEDIA:
- !screenshot, !video, !webcam — Media capture
- !sysinfo, !battery, !brightness — System info
- !ls, !get, !find — File navigation
- !web [query] — Web search
- !ai work/write/automate/summarize/research/insight — AI tasks
- !daily — Daily activity report
- !focus, !reminder, !task, !todo — Productivity
- !memory search — Search memory
- !solve [problem] — Problem solving
- !companion — Chat with companion
- !learn [topic] — Knowledge enrichment
- !scrape [url] — Web scraping
- !cd [path] — Change directory

RESPON JSON:
{{
  "plan": [
    {{"step": 1, "command": "!screenshot", "reason": "..."}},
    {{"step": 2, "command": "!ai research ...", "reason": "..."}}
  ],
  "estimated_duration": "5 menit",
  "risk_level": "low|medium|high"
}}
"""


class AutonomousAgent:
    def __init__(self):
        self.router = CommandRouter()
        self.running = False
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get(
            "NVIDIA_NIM_BASE_URL",
            "https://integrate.api.nvidia.com/v1",
        )
        self.nim_model = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")

    async def run(self, goal: str, user_id: str) -> str:
        self.running = True
        try:
            plan = await self._generate_plan(goal)
            if not plan or "plan" not in plan:
                return "❌ Gagal membuat rencana untuk goal tersebut."

            results = []
            for step in plan["plan"]:
                if not self.running:
                    results.append("⏹️ Agent dihentikan oleh user.")
                    break
                cmd = step["command"]
                reason = step.get("reason", "")
                results.append(f"📌 *Step {step['step']}:* {reason}\n`{cmd}`")
                try:
                    result = await self.router.route(cmd, user_id)
                    if isinstance(result, str):
                        results.append(f"  {result[:300]}")
                    elif isinstance(result, dict):
                        results.append(f"  ✅ {result.get('type', 'success')}")
                    else:
                        results.append("  ✅ Done")
                except Exception as e:
                    results.append(f"  ❌ Error: {e}")
                await asyncio.sleep(0.5)

            report = (
                f"🤖 *Autonomous Agent Report*\n"
                f"Goal: {goal}\n"
                f"Status: ✅ Completed\n"
                f"Steps: {len(plan.get('plan', []))}\n\n"
            ) + "\n".join(results)

            try:
                from agent.memory.manager import memory_manager
                memory_manager.remember(
                    f"Autonomous agent completed goal: {goal}\nResults: {report[:500]}",
                    source="autonomous_agent",
                    topic="agent_execution",
                    tags=["autonomous", "agent"],
                )
            except Exception:
                pass

            return report
        finally:
            self.running = False

    async def _generate_plan(self, goal: str) -> dict | None:
        prompt = AUTONOMOUS_PROMPT.format(goal=goal)
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.nim_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.nim_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.nim_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 2048,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                raw = resp.json()["choices"][0]["message"]["content"]
                json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                return json.loads(raw)
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            return None

    def stop(self):
        self.running = False


autonomous_agent = AutonomousAgent()
