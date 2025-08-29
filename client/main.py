"""Entry point for launching the monitoring agent GUI."""

from __future__ import annotations

import sys
from pathlib import Path

# Support running as ``python client/main.py`` by ensuring the repository root
# is on ``sys.path`` and then using absolute imports.
if __package__ is None or __package__ == "":  # pragma: no cover - runtime convenience
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from client.core.agent import MonitoringAgent
from client.gui.tray_app import MonitoringApp


def main() -> None:  # pragma: no cover - integration
    agent = MonitoringAgent()
    app = MonitoringApp(agent)
    app.run()


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
