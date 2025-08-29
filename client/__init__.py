"""Monitoring client package."""
from .core.agent import MonitoringAgent

try:  # Optional GUI dependencies
    from .gui.tray_app import MonitoringApp
except Exception:  # pragma: no cover - optional
    MonitoringApp = None

__all__ = ["MonitoringAgent", "MonitoringApp"]
