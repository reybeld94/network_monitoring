import platform
import socket
from .base_detector import BaseDetector


class HardwareDetector(BaseDetector):
    """Detector specialized in system hardware information."""

    def detect(self) -> dict:
        """Collect basic hardware details of the running host."""
        self.debug_log("Collecting hardware information")
        return {
            "agent_id": f"{socket.gethostname()}_{platform.node()}",
            "hostname": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "platform": platform.platform(),
        }
