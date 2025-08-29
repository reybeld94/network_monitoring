import threading
import time
from ..config.client_config import ClientConfig
from ..detectors.hardware_detector import HardwareDetector
from ..detectors.software_detector import SoftwareDetector
from ..detectors.backup_detector import BackupDetector
from ..utils.network_utils import post_json


class MonitoringAgent:
    """Coordinates detectors and reports data to the monitoring server."""

    def __init__(self, config: ClientConfig | None = None, debug_mode: bool = False):
        self.config = config or ClientConfig.load()
        self.debug_mode = debug_mode
        self.hardware = HardwareDetector(debug_mode)
        self.software = SoftwareDetector(debug_mode)
        self.backup = BackupDetector(debug_mode)
        self._running = False
        self._thread: threading.Thread | None = None

    def debug_log(self, msg: str) -> None:
        if self.debug_mode:
            print(f"[DEBUG] {msg}")

    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background monitoring thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def _run(self) -> None:
        while self._running:
            payload = {
                "system": self.hardware.detect(),
                "software": self.software.detect(),
                "backup": self.backup.detect(),
            }
            try:
                post_json(f"{self.config.server_url}/api/agents/monitoring-data", payload)
            except Exception as exc:  # pragma: no cover - network
                self.debug_log(f"Failed to send data: {exc}")
            time.sleep(60)
