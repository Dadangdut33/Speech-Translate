import tkinter as tk
from speech_translate.components.abstract.detached import AbstractDetachedSubtitleWindow


# Classes
class TlsWindow(AbstractDetachedSubtitleWindow):
    """Tcs Subtitle Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        super().__init__(master, "Translated Speech Subtitle Window", "tl")
