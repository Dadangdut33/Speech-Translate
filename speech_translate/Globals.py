__all__ = ["dir_project", "dir_setting", "dir_temp", "gClass", "fJson"]

import os
from multiprocessing import Process

from utils.Json import SettingJsonHandler

# ------------------ #
# Paths
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_assets: str = os.path.join(dir_project, "../assets")
dir_setting: str = os.path.join(dir_project, "../setting")
dir_temp: str = os.path.join(dir_project, "../temp")
dir_log: str = os.path.join(dir_project, "../log")
app_icon: str = os.path.join(dir_assets, "../icon.ico")
if not os.path.exists(app_icon):  # verify app_icon exist or not
    app_icon_missing = True
else:
    app_icon_missing = False
# ------------------ #
app_name: str = "Speech Translate"
fJson: SettingJsonHandler = SettingJsonHandler(os.path.join(dir_setting, "setting.json"), dir_setting, dir_temp, dir_log)
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

        # process
        self.dl_proc: None | Process = None
        self.tc_proc: None | Process = None
        self.tl_proc: None | Process = None

        # References to class
        self.tray = None  # tray
        self.mw = None  # main window
        self.sw = None  # setting window
        self.about = None  # about window
        self.detached_tcw = None  # detached transcribed window
        self.detached_tlw = None  # detached translated window

        # window
        self.cw = None  # console window

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

    def insertTbTranslated(self, textToAppend: str):
        """_summary_: Insert text to translated textbox. Will also check if the text is too long and will truncate it if it is.

        Args:
            textToAppend (str): Text to append
        """
        assert self.mw is not None
        currentText = self.getMwTextTl()
        # Main window textbox
        if len(currentText) > fJson.settingCache["textbox"]["mw_tl"]["max"]:
            # remove words from the start with length of the new text
            currentText = currentText[len(textToAppend) :]
            # add new text to the end
            currentText += textToAppend
            # update textbox
            self.mw.tb_translated.delete("1.0", "end")
            self.mw.tb_translated.insert("end", currentText)
        else:
            self.mw.tb_translated.insert("end", textToAppend)

    def insertDetachedTbTranscribed(self, textToAppend: str):
        """_summary_: Insert text to detached transcribed textbox. Will also check if the text is too long and will truncate it if it is.

        Args:
            textToAppend (str): Text to append
        """
        assert self.detached_tcw is not None
        currentText = self.getDetachedTextTc()
        # Main window textbox
        if len(currentText) > fJson.settingCache["textbox"]["detached_tc"]["max"]:
            # remove words from the start with length of the new text
            currentText = currentText[len(textToAppend) :]
            # add new text to the end
            currentText += textToAppend
            # update textbox
            self.detached_tcw.textbox.delete("1.0", "end")
            self.detached_tcw.textbox.insert("end", currentText)
        else:
            self.detached_tcw.textbox.insert("end", textToAppend)

    def insertDetachedTbTranslated(self, textToAppend: str):
        """_summary_: Insert text to detached translated textbox. Will also check if the text is too long and will truncate it if it is.

        Args:
            textToAppend (str): Text to append
        """
        assert self.detached_tlw is not None
        currentText = self.getDetachedTextTl()
        # Main window textbox
        if len(currentText) > fJson.settingCache["textbox"]["detached_tl"]["max"]:
            # remove words from the start with length of the new text
            currentText = currentText[len(textToAppend) :]
            # add new text to the end
            currentText += textToAppend
            # update textbox
            self.detached_tlw.textbox.delete("1.0", "end")
            self.detached_tlw.textbox.insert("end", currentText)
        else:
            self.detached_tlw.textbox.insert("end", textToAppend)

    def getMwTextTc(self) -> str:
        assert self.mw is not None
        return self.mw.tb_transcribed.get("1.0", "end")

    def getMwTextTl(self) -> str:
        assert self.mw is not None
        return self.mw.tb_translated.get("1.0", "end")

    def getDetachedTextTc(self) -> str:
        assert self.detached_tcw is not None
        return self.detached_tcw.textbox.get("1.0", "end")

    def getDetachedTextTl(self) -> str:
        assert self.detached_tlw is not None
        return self.detached_tlw.textbox.get("1.0", "end")


# ------------------ #
gClass: Globals = Globals()
