import os

from utils.Json import SettingJsonHandler


# ------------------ #
# Paths
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_setting: str = os.path.join(dir_project, "../setting")

# ------------------ #
class Globals:
    """
    Class containing all the static variables for the UI. It also contains some methods for the stuff to works.

    Stored like this in order to allow other file to use the same thing without circular import error.
    """

    def __init__(self):
        # Flags
        self.running = True

        # References to class
        self.mw = None
        self.tray = None


# ------------------ #
version = "1.0.0"
gClass = Globals()
fSetting = SettingJsonHandler(os.path.join(dir_setting, "setting.json"), dir_setting)
