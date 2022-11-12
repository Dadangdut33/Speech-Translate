__all__ = ["dir_project", "dir_setting", "dir_temp", "version", "gClass", "fJson"]

import os
from multiprocessing import Process

from utils.Json import SettingJsonHandler

# ------------------ #
# Paths
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_setting: str = os.path.join(dir_project, "../setting")
dir_temp: str = os.path.join(dir_project, "../temp")
app_icon: str = os.path.join(dir_project, "../assets/icon.ico")
if not os.path.exists(app_icon):  # verify app_icon exist or not
    app_icon_missing = True
else:
    app_icon_missing = False
# ------------------ #
version: str = "1.0.0"
app_name: str = "Speech Translate"
fJson: SettingJsonHandler = SettingJsonHandler(os.path.join(dir_setting, "setting.json"), dir_setting, dir_temp)
# ------------------ #
class Globals:
    """
    Class containing all the static variables for the UI. It also contains some methods for the stuff to works.

    Stored like this in order to allow other file to use the same thing without circular import error.
    """

    def __init__(self):
        # Flags
        self.running: bool = True
        self.recording: bool = False
        self.transcribing: bool = False
        self.translating: bool = False
        self.stop_tc: bool = False
        self.stop_tl: bool = False

        # process
        self.tc_proc: None | Process = None
        self.tl_proc: None | Process = None

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

    def enableStopTc(self):
        self.stop_tc = True

    def disableStopTc(self):
        self.stop_tc = False

    def enableStopTl(self):
        self.stop_tl = True

    def disableStopTl(self):
        self.stop_tl = False

    def insertTbTranscribed(self, textToAppend: str):
        """_summary_: Insert text to transcribed textbox. Will also check if the text is too long and will truncate it if it is.

        Args:
            textToAppend (str): Text to append
        """
        assert self.mw is not None
        currentText = self.getMwTextTc()
        # Main window textbox
        if len(currentText) > fJson.settingCache["textbox"]["mw_tc"]["max"]:
            # remove words from the start with length of the new text
            currentText = currentText[len(textToAppend) :]
            # add new text to the end
            currentText += textToAppend
            # update textbox
            self.mw.tb_transcribed.delete("1.0", "end")
            self.mw.tb_transcribed.insert("end", currentText)
        else:
            self.mw.tb_transcribed.insert("end", textToAppend)

    def insertTbTranslated(self, text: str):
        assert self.mw is not None
        self.mw.tb_translated.insert("end", text)

    def getMwTextTc(self) -> str:
        assert self.mw is not None
        return self.mw.tb_transcribed.get("1.0", "end")

    def getMwTextTl(self) -> str:
        assert self.mw is not None
        return self.mw.tb_translated.get("1.0", "end")


# ------------------ #
gClass: Globals = Globals()
