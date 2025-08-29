import tkinter as tk
from tkinter import ttk
from ..config.client_config import ClientConfig


class SettingsWindow(tk.Toplevel):
    """Simple configuration dialog allowing modification of the server URL."""

    def __init__(self, master=None, config: ClientConfig | None = None):
        self._root: tk.Tk | None = None
        if master is None:
            self._root = tk.Tk()
            self._root.withdraw()
            master = self._root
        super().__init__(master)
        self.title("Client Settings")
        self.resizable(False, False)
        self.config_obj = config or ClientConfig.load()
        ttk.Label(self, text="Server URL:").grid(row=0, column=0, padx=5, pady=5)
        self.url_var = tk.StringVar(value=self.config_obj.server_url)
        ttk.Entry(self, textvariable=self.url_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self, text="Save", command=self._save).grid(row=1, column=0, columnspan=2, pady=10)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _save(self) -> None:
        self.config_obj.server_url = self.url_var.get()
        self.config_obj.save()
        self._close()

    def _close(self) -> None:
        if self._root is not None:
            self._root.destroy()
        else:
            self.destroy()
