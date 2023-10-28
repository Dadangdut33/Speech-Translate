from tkinter import Tk

from speech_translate.ui.template.detached import SubtitleWindow


# Classes
class TlsWindow(SubtitleWindow):
    """Tcs Subtitle Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: Tk):
        super().__init__(master, "Translated Speech Subtitle Window", "tl")
