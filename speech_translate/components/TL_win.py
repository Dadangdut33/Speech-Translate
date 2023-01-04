from .Detached import AbstractDetachedWindow

# Classes
class TlsWindow(AbstractDetachedWindow):
    """Tcs Window"""

    # ----------------------------------------------------------------------
    def __init__(self):
        super().__init__("Translated Speech", "tl")
