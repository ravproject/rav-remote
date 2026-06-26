#!/usr/bin/env python3
"""Helper CLI untuk registrasi agent lokal saat setup hub."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


def register_local() -> int:
    from agent.fleet import register_agent_to_registry

    agent_id = os.environ.get("AGENT_ID", "hub")
    port = int(os.environ.get("AGENT_PORT", "8765"))
    api_key = os.environ.get("AGENT_API_KEY", "")
    if not api_key:
        print("AGENT_API_KEY tidak ditemukan di .env", file=sys.stderr)
        return 1

    register_agent_to_registry(agent_id, "localhost", port, api_key)
    print(f"Agent lokal '{agent_id}' terdaftar di registry (localhost:{port})")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "register-local"
    if cmd == "register-local":
        raise SystemExit(register_local())
    print(f"Perintah tidak dikenal: {cmd}", file=sys.stderr)
    raise SystemExit(1)
