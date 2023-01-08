from .Detached import AbstractDetachedWindow

# Classes
class TcsWindow(AbstractDetachedWindow):
    """Tcs Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master):
        super().__init__(master, "Transcribed Speech", "tc")
