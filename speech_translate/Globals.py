__all__ = ["dir_project", "dir_setting", "dir_temp", "version", "gClass", "fJson"]

import os

from utils.Json import SettingJsonHandler

# ------------------ #
# Paths
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_setting: str = os.path.join(dir_project, "../setting")
dir_temp: str = os.path.join(dir_project, "../temp")
app_icon: str = os.path.join(dir_project, "../assets/icon.ico")
# verify app_icon exist or not
if not os.path.exists(app_icon):
    app_icon_missing = True
else:
    app_icon_missing = False

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

        # window
        self.consoleWindow = None

    def enableRecording(self):
        self.recording = True

    def disableRecording(self):
        self.recording = False

    def enableTranscribing(self):
        self.transcribing = True

    def disableTranscribing(self):
        self.transcribing = False

    def enableTranslating(self):
        self.translating = True

    def disableTranslating(self):
        self.translating = False

    def insertTbTranscribed(self, text: str):
        assert self.mw is not None
        self.mw.tb_transcribed.insert("end", text)

    def insertTbTranslated(self, text: str):
        assert self.mw is not None
        self.mw.tb_translated.insert("end", text)


# ------------------ #
version: str = "1.0.0"
gClass: Globals = Globals()
fJson: SettingJsonHandler = SettingJsonHandler(os.path.join(dir_setting, "setting.json"), dir_setting, dir_temp)
app_name: str = "Speech Translate"
