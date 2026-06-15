"""
Agent Registry — Penyimpanan kredensial multi-agent.
Menggunakan CryptoManager untuk enkripsi at-rest.
"""
import json
import os
from security.crypto import crypto
from loguru import logger

REGISTRY_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "agent_registry.json")

class AgentRegistry:
    def __init__(self):
        self.agents = self._load()

    def _load(self) -> dict:
        if not os.path.exists(REGISTRY_FILE):
            return {}
        try:
            with open(REGISTRY_FILE, "r") as f:
                encrypted_data = f.read().strip()
                if not encrypted_data:
                    return {}
                decrypted_data = crypto.decrypt(encrypted_data)
                return json.loads(decrypted_data)
        except Exception as e:
            logger.error(f"Failed to load/decrypt agent registry: {e}")
            return {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
            json_data = json.dumps(self.agents)
            encrypted_data = crypto.encrypt(json_data)
            with open(REGISTRY_FILE, "w") as f:
                f.write(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to save/encrypt agent registry: {e}")

    def add_agent(self, agent_id: str, host: str, port: int, api_key: str):
        self.agents[agent_id] = {
            "host": host,
            "port": port,
            "api_key": api_key
        }
        self._save()
        logger.info(f"Agent {agent_id} added to registry.")

    def remove_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            self._save()
            logger.info(f"Agent {agent_id} removed from registry.")
            return True
        return False

    def get_agent(self, agent_id: str) -> dict:
        # Always reload to ensure we have the latest agents from disk
        self.agents = self._load()
        return self.agents.get(agent_id)

    def get_all(self) -> dict:
        self.agents = self._load()
        return self.agents

# Singleton instance
registry = AgentRegistry()
