from .Detached import AbstractDetachedWindow

# Classes
class TcsWindow(AbstractDetachedWindow):
    """Tcs Window"""

    # ----------------------------------------------------------------------
    def __init__(self):
        super().__init__("Transcribed Speech", "tc")
