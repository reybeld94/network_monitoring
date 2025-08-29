"""Client configuration utilities."""
from dataclasses import dataclass, field
from typing import Optional
from ..utils.system_utils import load_config, save_config


@dataclass
class ClientConfig:
    """Configuration values for the monitoring client."""
    server_url: str = "http://localhost:5000"
    path: str = "client_config.json"

    @classmethod
    def load(cls, path: Optional[str] = None) -> "ClientConfig":
        data = load_config(path or "client_config.json")
        return cls(**data) if data else cls()

    def save(self) -> None:
        save_config({"server_url": self.server_url}, self.path)
