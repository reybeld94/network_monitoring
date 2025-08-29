import subprocess
from .base_detector import BaseDetector


class BackupDetector(BaseDetector):
    """Detector for Windows backup status using ``wbadmin``."""

    def detect(self) -> dict:
        """Run ``wbadmin get versions`` and parse minimal details."""
        self.debug_log("Checking backup information with wbadmin")
        info = {"status": "unknown", "versions": []}
        try:
            result = subprocess.run(
                ["wbadmin", "get", "versions"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=30,
            )
            if result.returncode == 0:
                info["status"] = "found"
                info["output"] = result.stdout
            else:
                info["status"] = "error"
                info["error"] = result.stderr
        except Exception as exc:  # pragma: no cover - platform specific
            info["status"] = "error"
            info["error"] = str(exc)
        return info
