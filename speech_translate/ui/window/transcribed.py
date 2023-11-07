from tkinter import Tk

from speech_translate.ui.template.detached import SubtitleWindow


# Classes
class TcsWindow(SubtitleWindow):
    """Tcs Subtitle Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: Tk):
        super().__init__(master, "Transcribed Speech Subtitle Window", "tc")
