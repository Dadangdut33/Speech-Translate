__all__ = ["dir_project", "dir_setting", "dir_temp", "dir_log", "dir_assets", "gClass", "fJson", "app_icon", "app_name"]

import os
import platform
import ast
import shlex
from multiprocessing import Process, Queue
from typing import Optional
from time import sleep

if platform.system() == "Windows":
    import pyaudiowpatch as pyaudio
else:
    import pyaudio  # type: ignore

from .utils.Json import SettingJsonHandler

# ------------------ #
# Paths
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_setting: str = os.path.join(dir_project, "../setting")
dir_temp: str = os.path.join(dir_project, "../temp")
dir_log: str = os.path.join(dir_project, "../log")
dir_assets: str = os.path.join(dir_project, "../assets")
app_icon: str = os.path.join(dir_assets, "icon.ico")
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
        self.dl_proc: Optional[Process] = None
        self.tc_proc: Optional[Process] = None
        self.tl_proc: Optional[Process] = None

        # References to class
        self.tray = None  # tray
        self.mw = None  # main window
        self.sw = None  # setting window
        self.about = None  # about window
        self.ex_tcw = None  # detached transcribed window
        self.ex_tlw = None  # detached translated window

        # window
        self.cw = None  # console window

        # record stream
        self.stream: Optional[pyaudio.Stream] = None
        self.data_queue = Queue()
        self.max_energy: int = 5000

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

    def insertMwTbTc(self, textToAppend: str):
        """_summary_: Insert text to transcribed textbox. Will also check if the text is too long and will truncate it if it is.
        Separator should be added in the arguments (already in textToAppend)

        Args:
            textToAppend (str): Text to append
        """
        assert self.mw is not None
        currentText = self.getMwTextTc()
        # Main window textbox
        if fJson.settingCache["tb_mw_tc_max"] != 0 and len(currentText) > fJson.settingCache["tb_mw_tc_max"]:  # if not infinite and text too long
            # remove words from the start with length of the new text
            currentText = currentText[len(textToAppend) :]
            # add new text to the end
            currentText += textToAppend
            # update textbox
            self.mw.tb_transcribed.delete("1.0", "end")
            self.mw.tb_transcribed.insert("end", currentText)
        else:
            self.mw.tb_transcribed.insert("end", textToAppend)

        self.mw.tb_transcribed.see("end")

    def insertMwTbTl(self, textToAppend: str):
        """_summary_: Insert text to translated textbox. Will also check if the text is too long and will truncate it if it is.
        Separator should be added in the arguments (already in textToAppend)

        Args:
            textToAppend (str): Text to append
        """
        assert self.mw is not None
        currentText = self.getMwTextTl()
        # Main window textbox
        if fJson.settingCache["tb_mw_tl_max"] != 0 and len(currentText) > fJson.settingCache["tb_mw_tl_max"]:  # if not infinite and text is too long
            # remove words from the start with length of the new text
            currentText = currentText[len(textToAppend) :]
            # add new text to the end
            currentText += textToAppend
            # update textbox
            self.mw.tb_translated.delete("1.0", "end")
            self.mw.tb_translated.insert("end", currentText)
        else:
            self.mw.tb_translated.insert("end", textToAppend)

        self.mw.tb_transcribed.see("end")

    def insertExTbTc(self, textToAppend: str):
        """_summary_: Insert text to detached transcribed textbox. Will also check if the text is too long and will truncate it if it is.
        Separator is added here.

        Args:
            textToAppend (str): Text to append
        """
        assert self.ex_tcw is not None
        currentText = self.getDetachedTextTc().strip()
        textToAppend = textToAppend.strip()
        # Main window textbox
        if fJson.settingCache["tb_ex_tc_max"] != 0 and len(currentText) > fJson.settingCache["tb_ex_tc_max"]:  # if not infinite and text is too long
            currentText = currentText[len(textToAppend) :]  # remove words from the start with length of the new text
            currentText += ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"]))  # add separator
            currentText += textToAppend  # add new text to the end
            self.ex_tcw.curText = currentText  # update textbox
        else:
            currentText += ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"]))  # add new text to the end
            currentText += textToAppend  # add new text to the end
            self.ex_tcw.curText = currentText

        self.ex_tcw.update_text()

    def insertExTbTl(self, textToAppend: str):
        """_summary_: Insert text to detached translated textbox. Will also check if the text is too long and will truncate it if it is.
        Separator is added here.

        Args:
            textToAppend (str): Text to append
        """
        assert self.ex_tlw is not None
        currentText = self.getDetachedTextTl().strip()
        textToAppend = textToAppend.strip()
        # Main window textbox
        if fJson.settingCache["tb_ex_tl_max"] != 0 and len(currentText) > fJson.settingCache["tb_ex_tl_max"]:  # if not infinite and text is too long
            currentText = currentText[len(textToAppend) :]  # remove words from the start with length of the new text
            currentText += ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"]))  # add separator
            currentText += textToAppend  # add new text to the end
            self.ex_tlw.curText = currentText  # update textbox
        else:
            currentText += ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"]))  # add new text to the end
            currentText += textToAppend  # add new text to the end
            self.ex_tlw.curText = currentText
        self.ex_tlw.update_text()

    def getMwTextTc(self) -> str:
        assert self.mw is not None
        return self.mw.tb_transcribed.get("1.0", "end")

    def getMwTextTl(self) -> str:
        assert self.mw is not None
        return self.mw.tb_translated.get("1.0", "end")

    def clearMwTc(self):
        assert self.mw is not None
        self.mw.tb_transcribed.delete("1.0", "end")

    def clearMwTl(self):
        assert self.mw is not None
        self.mw.tb_translated.delete("1.0", "end")

    def getDetachedTextTc(self) -> str:
        assert self.ex_tcw is not None
        self.ex_tcw.get_cur_text()
        sleep(0.1)
        return self.ex_tcw.curText

    def getDetachedTextTl(self) -> str:
        assert self.ex_tlw is not None
        self.ex_tlw.get_cur_text()
        sleep(0.1)
        return self.ex_tlw.curText

    def clearDetachedTc(self):
        assert self.ex_tcw is not None
        self.ex_tcw.curText = ""
        self.ex_tcw.update_text()

    def clearDetachedTl(self):
        assert self.ex_tlw is not None
        self.ex_tlw.curText = ""
        self.ex_tlw.update_text()


# ------------------ #
gClass: Globals = Globals()
