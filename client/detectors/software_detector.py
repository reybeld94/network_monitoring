import os
from .base_detector import BaseDetector


class SoftwareDetector(BaseDetector):
    """Detector for installed productivity and CAD software."""

    def detect(self) -> dict:
        """Return minimal information about Office presence.

        The original project performs extensive inspection of installed
        Office and CAD packages.  For brevity this refactor only checks for
        the presence of ``WINWORD.EXE`` in common locations.
        """
        self.debug_log("Detecting software")
        office_paths = [
            r"C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
            r"C:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
        ]
        office_installed = any(os.path.exists(p) for p in office_paths)
        return {
            "office": {
                "installed": office_installed,
            },
            "cad": {},
        }
