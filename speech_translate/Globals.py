__all__ = ["dir_project", "dir_setting", "dir_temp", "version", "gClass", "fJson"]

import os

from utils.Json import SettingJsonHandler
from whisper import tokenizer

# ------------------ #
# Paths
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_setting: str = os.path.join(dir_project, "../setting")
dir_temp: str = os.path.join(dir_project, "../temp")
app_icon: str = os.path.join(dir_project, "../assets/icon.ico")

# ------------------ #
class Globals:
    """
    Class containing all the static variables for the UI. It also contains some methods for the stuff to works.

    Stored like this in order to allow other file to use the same thing without circular import error.
    """

    def __init__(self):
        # Flags
        self.running = True
        self.recording = False
        self.transcribing = False
        self.translating = False

        # References to class
        self.mw = None
        self.tray = None


# ------------------ #
version: str = "1.0.0"
gClass: Globals = Globals()
fJson: SettingJsonHandler = SettingJsonHandler(os.path.join(dir_setting, "setting.json"), dir_setting, dir_temp)
