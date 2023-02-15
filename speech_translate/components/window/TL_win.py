import tkinter as tk
from speech_translate.components.abstract.Detached import AbstractDetachedWindow


# Classes
class TlsWindow(AbstractDetachedWindow):
    """Tcs Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        super().__init__(master, "Translated Speech", "tl")
