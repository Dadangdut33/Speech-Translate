from .Detached import AbstractDetachedWindow

# Classes
class TlsWindow(AbstractDetachedWindow):
    """Tcs Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master):
        super().__init__(master, "Translated Speech", "tl")
