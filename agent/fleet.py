"""
Fleet pairing — auto-register agents ke hub tanpa CLI manual.
"""
import os
import socket
import asyncio

import httpx
from loguru import logger
from pydantic import BaseModel


class FleetRegisterRequest(BaseModel):
    agent_id: str
    host: str
    port: int
    api_key: str
    fleet_key: str


def detect_lan_ip() -> str:
    """Deteksi IP LAN utama untuk registrasi otomatis."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def validate_fleet_key(fleet_key: str) -> bool:
    expected = os.environ.get("FLEET_PAIRING_KEY", "")
    return bool(expected) and fleet_key == expected


def register_agent_to_registry(agent_id: str, host: str, port: int, api_key: str) -> None:
    from bot.agent_registry import registry

    registry.add_agent(agent_id, host, port, api_key)


async def register_with_hub(retries: int = 3) -> None:
    """Agent satellite: daftarkan diri ke hub saat startup."""
    if os.environ.get("RAV_MODE", "hub") != "agent":
        return

    hub_url = os.environ.get("HUB_URL", "").rstrip("/")
    fleet_key = os.environ.get("FLEET_PAIRING_KEY", "")
    agent_id = os.environ.get("AGENT_ID", "agent")
    api_key = os.environ.get("AGENT_API_KEY", "")
    port = int(os.environ.get("AGENT_PORT", "8765"))

    if not hub_url or not fleet_key:
        logger.warning("Mode agent: HUB_URL atau FLEET_PAIRING_KEY kosong — skip auto-register")
        return

    host = detect_lan_ip()
    payload = {
        "agent_id": agent_id,
        "host": host,
        "port": port,
        "api_key": api_key,
        "fleet_key": fleet_key,
    }

    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{hub_url}/fleet/register", json=payload)
            if resp.status_code == 200:
                logger.info(f"✅ Terdaftar ke hub sebagai '{agent_id}' ({host}:{port})")
                return
            logger.warning(
                f"Gagal register ke hub (attempt {attempt}/{retries}): "
                f"{resp.status_code} {resp.text[:200]}"
            )
        except Exception as e:
            logger.warning(f"Hub tidak reachable (attempt {attempt}/{retries}): {e}")

        if attempt < retries:
            await asyncio.sleep(5)

    logger.error(
        f"Tidak bisa mendaftar ke hub {hub_url}. "
        "Pastikan hub sudah jalan dan kode pairing benar."
    )


async def register_with_hub_loop() -> None:
    """Background retry agar agent bisa connect setelah hub nyala."""
    await register_with_hub(retries=5)
    while os.environ.get("RAV_MODE", "hub") == "agent":
        await asyncio.sleep(120)
        await register_with_hub(retries=1)
