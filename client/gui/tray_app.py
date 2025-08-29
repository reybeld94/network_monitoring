import threading
from PIL import Image, ImageDraw
import pystray
from ..core.agent import MonitoringAgent
from .settings_window import SettingsWindow


class MonitoringApp:
    """Minimal system tray application wrapping ``MonitoringAgent``."""

    def __init__(self, agent: MonitoringAgent):
        self.agent = agent
        self.icon = pystray.Icon("monitoring-client")
        image = Image.new("RGB", (64, 64), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 64, 64), fill="green")
        self.icon.icon = image
        self.icon.menu = pystray.Menu(
            pystray.MenuItem("Settings", self.open_settings),
            pystray.MenuItem("Exit", self.stop),
        )

    def open_settings(self):  # pragma: no cover - GUI
        def _run() -> None:
            window = SettingsWindow()
            window.mainloop()

        threading.Thread(target=_run, daemon=True).start()

    def stop(self):  # pragma: no cover - GUI
        self.icon.stop()

    def run(self):  # pragma: no cover - GUI
        threading.Thread(target=self.agent.start, daemon=True).start()
        self.icon.run()
