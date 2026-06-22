#!/usr/bin/env python3
"""
CLI Tool untuk mengelola Agent Registry secara offline.
Menghindari kebocoran API Key via riwayat chat Telegram.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from bot.agent_registry import registry

def print_help():
    print("RAV-REMOTE Agent Manager")
    print("Usage:")
    print("  python manage_agents.py list")
    print("  python manage_agents.py add <agent_id> <host> <port> <api_key>")
    print("  python manage_agents.py remove <agent_id>")

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "list":
        agents = registry.get_all()
        if not agents:
            print("No agents registered.")
        else:
            print(f"Registered Agents ({len(agents)}):")
            for agent_id, data in agents.items():
                print(f" - [{agent_id}] -> http://{data['host']}:{data['port']}")

    elif command == "add":
        if len(sys.argv) != 6:
            print("Usage: python manage_agents.py add <agent_id> <host> <port> <api_key>")
            sys.exit(1)
        
        agent_id = sys.argv[2]
        host = sys.argv[3]
        try:
            port = int(sys.argv[4])
        except ValueError:
            print("Error: Port must be an integer.")
            sys.exit(1)
        api_key = sys.argv[5]

        registry.add_agent(agent_id, host, port, api_key)
        print(f"Successfully added agent '{agent_id}'.")

    elif command == "remove":
        if len(sys.argv) != 3:
            print("Usage: python manage_agents.py remove <agent_id>")
            sys.exit(1)
        
        agent_id = sys.argv[2]
        if registry.remove_agent(agent_id):
            print(f"Successfully removed agent '{agent_id}'.")
        else:
            print(f"Agent '{agent_id}' not found.")

    else:
        print_help()

if __name__ == "__main__":
    main()
