class BaseDetector:
    """Base class for all monitoring detectors.

    Parameters
    ----------
    debug_mode: bool, optional
        Enables debug logging when set to True.
    """
    def __init__(self, debug_mode: bool = False) -> None:
        self.debug_mode = debug_mode

    def debug_log(self, message: str) -> None:
        """Print debug messages when debug mode is enabled."""
        if self.debug_mode:
            print(f"[DEBUG] {message}")

    def detect(self):  # pragma: no cover - abstract method
        """Perform detection and return structured data.

        Subclasses must implement this method.
        """
        raise NotImplementedError
