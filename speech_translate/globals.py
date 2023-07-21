import os
import platform
import ast
import shlex
import arabic_reshaper
from tkinter import ttk
from threading import Thread
from typing import Optional, List, TYPE_CHECKING
from ._path import dir_temp, dir_log, dir_export, dir_user
from ._contants import SUBTITLE_PLACEHOLDER, RESHAPE_LANG_LIST
from .utils.setting import SettingJson

if TYPE_CHECKING: # Forward declaration for type hinting
    from .components.window.main import MainWindow, AppTray
    from .components.window.setting import SettingWindow  
    from .components.window.about import AboutWindow  
    from .components.window.log import LogWindow
    from .components.window.transcribed import TcsWindow
    from .components.window.translated import TlsWindow

if platform.system() == "Windows":
    from multiprocessing import Queue
    import pyaudiowpatch as pyaudio
else:
    from .utils.custom_queue import MyQueue as Queue  # to get qsize
    import pyaudio  # type: ignore

# ------------------ #
sj: SettingJson = SettingJson(os.path.join(dir_user, "setting.json"), dir_user, [dir_temp, dir_log, dir_export])

# ------------------ #
class GlobalClass:
    """
    Class containing all the static variables for the UI. It also contains some methods for the stuff to works.

    Stored like this in order to allow other file to use the same thing without circular import error.
    """

    def __init__(self):
        # Flags
        self.running: bool = True
        self.recording: bool = False
        self.paused: bool = False
        self.transcribing: bool = False
        self.translating: bool = False

        # Style
        self.native_theme: str = ""
        self.theme_lists: List[str] = []
        self.style: Optional[ttk.Style] = None

        # model download
        self.dl_thread: Optional[Thread] = None
        self.cancel_dl: bool = False

        self.cw = None  # Console window
        # References to class
        self.tray: Optional[AppTray] = None
        """Tray app class"""
        self.mw: Optional[MainWindow] = None
        """Main window class"""
        self.sw: Optional[SettingWindow] = None
        """Setting window class"""
        self.lw: Optional[LogWindow] = None
        """Log window class"""
        self.about: Optional[AboutWindow] = None
        """About window class"""
        self.ex_tcw: Optional[TcsWindow] = None
        """Detached transcribed window class"""
        self.ex_tlw: Optional[TlsWindow] = None
        """Detached translated window class"""

        # record stream
        self.stream: Optional[pyaudio.Stream] = None
        self.data_queue = Queue()
        self.current_energy: int = 0
        self.current_rec_status = ""
        self.auto_detected_lang = "~"

        # file process
        self.file_tced_counter: int = 0
        self.file_tled_counter: int = 0

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
        """Insert text to transcribed textbox. Will also check if the text is too long and will truncate it if it is.
        Separator should be added in the arguments (already in textToAppend)

        Parameters
        ---
        textToAppend: str
            Text to append
        """
        assert self.mw is not None
        currentText = self.getMwTextTc()
        # Main window textbox
        if sj.cache["tb_mw_tc_max"] != 0 and len(currentText) > sj.cache["tb_mw_tc_max"]:  # if not infinite and text too long
            # remove words from the start with length of the new text
            # then add new text to the end
            currentText = currentText[len(textToAppend) :]
            currentText += textToAppend
            textToAppend = currentText
            self.mw.tb_transcribed.delete("1.0", "end")

        if sj.cache["sourceLang"].lower() in RESHAPE_LANG_LIST:
            textToAppend = arabic_reshaper.reshape(textToAppend)

        self.mw.tb_transcribed.insert("end", textToAppend)
        self.mw.tb_transcribed.see("end")

    def insertMwTbTl(self, textToAppend: str):
        """Insert text to translated textbox. Will also check if the text is too long and will truncate it if it is.
        Separator should be added in the arguments (already in textToAppend)

        Parameters
        ---
        textToAppend: str
            Text to append
        """
        assert self.mw is not None
        currentText = self.getMwTextTl()
        # Main window textbox
        if sj.cache["tb_mw_tl_max"] != 0 and len(currentText) > sj.cache["tb_mw_tl_max"]:  # if not infinite and text is too long
            # remove words from the start with length of the new text
            # then add new text to the end
            currentText = currentText[len(textToAppend) :]
            currentText += textToAppend
            textToAppend = currentText
            self.mw.tb_translated.delete("1.0", "end")

        if sj.cache["sourceLang"].lower() in RESHAPE_LANG_LIST:
            textToAppend = arabic_reshaper.reshape(textToAppend)

        self.mw.tb_translated.insert("end", textToAppend)
        self.mw.tb_translated.see("end")

    def insertExTbTc(self, textToAppend: str):
        """Insert text to detached transcribed textbox. Will also check if the text is too long and will truncate it if it is.
        Separator is added here.

        Parameters
        ---
        textToAppend: str
            Text to append
        """
        assert self.ex_tcw is not None
        currentText = self.ex_tcw.labelText.cget("text").strip()
        textToAppend = textToAppend.strip()
        # Main window textbox
        if sj.cache["tb_ex_tc_max"] != 0 and len(currentText) > sj.cache["tb_ex_tc_max"]:  # if not infinite and text is too long
            # remove words from the start with length of the new text
            # then add new text to the end
            currentText = currentText[len(textToAppend) :]
            currentText += textToAppend
            textToAppend = currentText  # set new text
        else:
            textToAppend += ast.literal_eval(shlex.quote(sj.cache["separate_with"]))  # set new text

        if sj.cache["sourceLang"].lower() in RESHAPE_LANG_LIST:
            textToAppend = arabic_reshaper.reshape(textToAppend)

        self.ex_tcw.labelText.config(text=textToAppend)
        self.ex_tcw.check_height_resize()

    def insertExTbTl(self, textToAppend: str):
        """Insert text to detached translated textbox. Will also check if the text is too long and will truncate it if it is.
        Separator is added here.

        Parameters
        ---
        textToAppend: str
            Text to append
        """
        assert self.ex_tlw is not None
        currentText = self.ex_tlw.labelText.cget("text").strip()
        textToAppend = textToAppend.strip()
        # Main window textbox
        if sj.cache["tb_ex_tl_max"] != 0 and len(currentText) > sj.cache["tb_ex_tl_max"]:  # if not infinite and text is too long
            currentText = currentText[len(textToAppend) :]  # remove words from the start with length of the new text
            currentText += textToAppend  # add new text to the end
            textToAppend = currentText  # set new text
        else:
            textToAppend += ast.literal_eval(shlex.quote(sj.cache["separate_with"]))  # set new text

        if sj.cache["sourceLang"].lower() in RESHAPE_LANG_LIST:
            textToAppend = arabic_reshaper.reshape(textToAppend)

        self.ex_tlw.labelText.config(text=textToAppend)
        self.ex_tlw.check_height_resize()

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

    def clearExTc(self):
        assert self.ex_tcw is not None
        self.ex_tcw.labelText.config(text=SUBTITLE_PLACEHOLDER)

    def clearExTl(self):
        assert self.ex_tlw is not None
        self.ex_tlw.labelText.config(text=SUBTITLE_PLACEHOLDER)


# ------------------ #
gc: GlobalClass = GlobalClass()
