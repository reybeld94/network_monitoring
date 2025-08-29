from .core.agent import MonitoringAgent
from .gui.tray_app import MonitoringApp


def main() -> None:  # pragma: no cover - integration
    agent = MonitoringAgent()
    app = MonitoringApp(agent)
    app.run()


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
