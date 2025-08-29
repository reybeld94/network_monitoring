"""Basic server configuration values."""
from dataclasses import dataclass


@dataclass
class ServerConfig:
    database_uri: str = "sqlite:///monitoring.db"
