"""Hardware detection utilities including service tag lookup."""

import csv
import io
import platform
import socket
import subprocess
from typing import Dict

from .base_detector import BaseDetector


class HardwareDetector(BaseDetector):
    """Detector specialized in system hardware information."""

    def detect(self) -> dict:
        """Collect basic hardware details of the running host."""
        self.debug_log("Collecting hardware information")
        info = {
            "agent_id": f"{socket.gethostname()}_{platform.node()}",
            "hostname": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "platform": platform.platform(),
        }
        info.update(self.get_service_tag())
        return info

    # ------------------------------------------------------------------
    # Service tag detection
    # ------------------------------------------------------------------
    def get_service_tag(self) -> Dict[str, str | None]:
        """Detect service tag using multiple methods."""
        service_tag_info = {
            "service_tag": None,
            "serial_number": None,
            "manufacturer": None,
            "model": None,
            "detection_method": None,
            "bios_serial": None,
            "baseboard_serial": None,
        }

        try:
            result = self.get_service_tag_wmic()
            if result.get("service_tag"):
                return result

            result = self.get_service_tag_powershell()
            if result.get("service_tag"):
                return result

            result = self.get_service_tag_registry()
            if result.get("service_tag"):
                return result

        except Exception as exc:  # pragma: no cover - defensive
            self.debug_log(f"Error in service tag detection: {exc}")

        return service_tag_info

    # Helper to run subprocess with common options
    def _run(self, cmd: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)

    def get_service_tag_wmic(self) -> Dict[str, str | None]:
        """Detection using WMIC commands."""
        info = {
            "service_tag": None,
            "serial_number": None,
            "manufacturer": None,
            "model": None,
            "detection_method": None,
            "bios_serial": None,
            "baseboard_serial": None,
        }

        try:
            cs = self._run(["wmic", "computersystem", "get", "Manufacturer,Model,Name", "/format:csv"])
            bios = self._run(["wmic", "bios", "get", "SerialNumber", "/format:csv"])
            base = self._run(["wmic", "baseboard", "get", "SerialNumber", "/format:csv"])

            reader = csv.DictReader(io.StringIO(cs.stdout.strip()))
            row = next(reader, {})
            manufacturer = row.get("Manufacturer")
            model = row.get("Model")

            bios_reader = csv.DictReader(io.StringIO(bios.stdout.strip()))
            bios_row = next(bios_reader, {})
            bios_serial = bios_row.get("SerialNumber")

            base_reader = csv.DictReader(io.StringIO(base.stdout.strip()))
            base_row = next(base_reader, {})
            baseboard_serial = base_row.get("SerialNumber")

            serial = bios_serial or baseboard_serial
            service_tag = serial
            if manufacturer and manufacturer.lower().startswith("dell"):
                service_tag = bios_serial

            info.update(
                {
                    "service_tag": service_tag,
                    "serial_number": serial,
                    "manufacturer": manufacturer,
                    "model": model,
                    "detection_method": "wmic",
                    "bios_serial": bios_serial,
                    "baseboard_serial": baseboard_serial,
                }
            )
        except Exception as exc:
            self.debug_log(f"WMIC detection failed: {exc}")

        return info

    def get_service_tag_powershell(self) -> Dict[str, str | None]:
        """Detection using PowerShell as fallback."""
        info = {
            "service_tag": None,
            "serial_number": None,
            "manufacturer": None,
            "model": None,
            "detection_method": None,
            "bios_serial": None,
            "baseboard_serial": None,
        }

        try:
            ps_script = (
                "$system = Get-WmiObject -Class Win32_ComputerSystem;"
                "$bios = Get-WmiObject -Class Win32_BIOS;"
                "$base = Get-WmiObject -Class Win32_BaseBoard;"
                "Write-Output \"$($system.Manufacturer),$($system.Model),$($bios.SerialNumber),$($base.SerialNumber)\""
            )
            proc = self._run(["powershell", "-NoProfile", "-Command", ps_script])
            parts = [p.strip() for p in proc.stdout.strip().split(",")]
            if len(parts) >= 4:
                manufacturer, model, bios_serial, baseboard_serial = parts[:4]
                serial = bios_serial or baseboard_serial
                service_tag = serial
                if manufacturer and manufacturer.lower().startswith("dell"):
                    service_tag = bios_serial
                info.update(
                    {
                        "service_tag": service_tag,
                        "serial_number": serial,
                        "manufacturer": manufacturer or None,
                        "model": model or None,
                        "detection_method": "powershell",
                        "bios_serial": bios_serial or None,
                        "baseboard_serial": baseboard_serial or None,
                    }
                )
        except Exception as exc:
            self.debug_log(f"PowerShell detection failed: {exc}")

        return info

    def get_service_tag_registry(self) -> Dict[str, str | None]:
        """Detection using Windows registry (last resort)."""
        # For now we return empty info as placeholder since registry access
        # is not required for tests or non-Windows environments.
        return {
            "service_tag": None,
            "serial_number": None,
            "manufacturer": None,
            "model": None,
            "detection_method": None,
            "bios_serial": None,
            "baseboard_serial": None,
        }
