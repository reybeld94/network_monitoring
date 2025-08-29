import json
import os
import socket
import uuid


def generate_agent_id() -> str:
    """Generate a unique agent identifier using hostname and MAC address."""
    hostname = socket.gethostname()
    mac = hex(uuid.getnode())[2:]
    return f"{hostname}_{mac}"


def load_config(path: str = "client_config.json") -> dict:
    """Load configuration data from *path* if it exists."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_config(config: dict, path: str = "client_config.json") -> None:
    """Persist *config* to *path* in JSON format."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
