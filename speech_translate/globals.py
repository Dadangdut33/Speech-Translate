import os
from ast import literal_eval
from platform import system
from shlex import quote
from threading import Lock, Thread
from tkinter import ttk
from typing import TYPE_CHECKING, List, Literal, Optional, Union
from warnings import simplefilter

import tqdm
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from numba.core.errors import NumbaDeprecationWarning, NumbaPendingDeprecationWarning

from ._constants import SUBTITLE_PLACEHOLDER
from ._path import dir_debug, dir_export, dir_log, dir_temp, dir_user
from .utils.setting import SettingJson

if system() == "Windows":
    from multiprocessing import Queue

    import pyaudiowpatch as pyaudio
else:
    import pyaudio  # type: ignore

    # to get qsize on platform other than windows
    from .utils.custom_queue import MyQueue as Queue

# remove numba warnings
simplefilter("ignore", category=NumbaDeprecationWarning)
simplefilter("ignore", category=NumbaPendingDeprecationWarning)

# Disabling tqdm globally by Defining a custom dummy class that suppresses tqdm's behavior


class DummyTqdm:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def update(self, n=1):
        pass


# Monkey-patch tqdm with the DummyTqdm class
tqdm.tqdm = DummyTqdm

# Forward declaration for type hinting
if TYPE_CHECKING:
    from .components.window.about import AboutWindow
    from .components.window.log import LogWindow
    from .components.window.main import AppTray, MainWindow
    from .components.window.setting import SettingWindow
    from .components.window.transcribed import TcsWindow
    from .components.window.translated import TlsWindow

# ------------------ #
sj: SettingJson = SettingJson(os.path.join(dir_user, "setting.json"), dir_user, [dir_temp, dir_log, dir_export, dir_debug])


class GlobalClass:
    """
    Class containing all the static variables for the UI. It also contains some methods for the stuff to works.

    Stored like this in order to allow other file to use the same thing without circular import error.
    """
    def __init__(self):
        self.cuda: str = ""
        self.running_after_id: str = ""

        # Flags
        self.running: bool = True
        self.recording: bool = False
        self.transcribing: bool = False
        self.translating: bool = False

        # Style
        self.native_theme: str = ""
        self.theme_lists: List[str] = []
        self.style: Optional[ttk.Style] = None

        # model download
        self.dl_thread: Optional[Thread] = None
        self.cancel_dl: bool = False

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
        self.data_queue: Queue[bytes] = Queue()  # type: ignore
        self.current_rec_status: str = ""
        self.auto_detected_lang: str = "~"
        self.tc_lock: Optional[Lock] = None

        # file process
        self.file_tced_counter: int = 0
        self.file_tled_counter: int = 0

    def enable_rec(self):
        self.recording = True

    def disable_rec(self):
        self.recording = False

    def enable_tc(self):
        self.transcribing = True

    def disable_tc(self):
        self.transcribing = False

    def enable_tl(self):
        self.translating = True

    def disable_tl(self):
        self.translating = False

    def get_separator(self):
        return literal_eval(quote(sj.cache["separate_with"]))

    def insert_result_mw(self, textToAppend, mode: Literal["tc", "tl"]):
        """Insert text to transcribed textbox. Will also check if the text is too long and will truncate it if it is.

        Parameters
        ---
        textToAppend
            Text to append
        mode: Literal["tc", "tl"]
            Mode to insert the text to. "tc" for transcribed textbox, "tl" for translated textbox
        """
        assert self.mw is not None
        op_dic = {"tc": [self.get_mw_tc, self.mw.tb_transcribed], "tl": [self.get_mw_tl, self.mw.tb_translated]}
        get_text = op_dic[mode][0]
        tb = op_dic[mode][1]

        separator = self.get_separator()
        currentText = get_text()
        # if not infinite and text too long
        # remove words from the start with length of the new text
        # then add new text to the end
        if sj.cache[f"tb_mw_{mode}_limit_max"] and len(currentText) > sj.cache[f"tb_mw_{mode}_max"]:
            currentText = currentText[len(textToAppend):]
            currentText += textToAppend
            textToAppend = currentText
            tb.delete("1.0", "end")

        if sj.cache["parse_arabic"]:
            textToAppend = str(get_display(reshape(textToAppend)))

        # if it has limit per sentence, break it into multiple sentences with
        # character limitation for each sentence set by the user.
        if sj.cache[f"tb_mw_{mode}_limit_max_per_line"]:
            currentText = currentText.split("\n")  # split it by line
            lastLine = currentText[-1]  # get the last line
            if lastLine != "":  # if the last line is not empty, add a new line
                tb.insert("end", "\n")

            # split the text to append by line
            textToAppend = textToAppend.split("\n")

            # loop through the text to append
            for line in textToAppend:
                if line != "":  # line is not empty
                    # too long, cut it into multiple lines
                    if len(line) > sj.cache[f"tb_mw_{mode}_max_per_line"]:
                        # split the line into multiple lines with the max length of the line set by the user
                        line = [
                            line[i:i + sj.cache[f"tb_mw_{mode}_max_per_line"]]
                            for i in range(0, len(line), sj.cache[f"tb_mw_{mode}_max_per_line"])
                        ]
                        # loop through the new lines
                        for newLine in line:
                            if newLine != "":  # not empty
                                # insert the new line
                                tb.insert("end", newLine + separator)
                    else:
                        # if the line is not too long, insert it
                        tb.insert("end", line + separator)
        else:
            tb.insert("end", textToAppend + separator)

        tb.see("end")

    def insert_result_ex(self, textToAppend, mode: Literal["tc", "tl"]):
        """
        Insert text to detached transcribed textbox. Will also check if
        the text is too long and will truncate it if it is. Separator is also added here.

        Parameters
        ---
        textToAppend
            Text to append
        """
        assert self.ex_tcw and self.ex_tlw is not None
        op_dic = {"tc": [self.get_ex_tc, self.ex_tcw], "tl": [self.get_ex_tl, self.ex_tlw]}
        get_text = op_dic[mode][0]
        ex: Union[TcsWindow, TlsWindow] = op_dic[mode][1]

        separator = self.get_separator()
        currentText = get_text()
        # if not infinite and text too long
        # remove words from the start with length of the new text
        # then add new text to the end
        if sj.cache[f"tb_ex_{mode}_limit_max"] and len(currentText) > sj.cache[f"tb_ex_{mode}_max"]:
            currentText = currentText[len(textToAppend):]
            currentText += textToAppend
            textToAppend = currentText

        if sj.cache["parse_arabic"]:
            textToAppend = str(get_display(reshape(textToAppend)))

        # if it has limit per sentence, break it into multiple sentences with
        # character limitation for each sentence set by the user.
        if sj.cache[f"tb_ex_{mode}_limit_max_per_line"]:
            # split the text to append by line
            splited = textToAppend.split("\n")
            textToAppend = ""

            # loop through the text to append
            for line in splited:
                if line != "":  # line is not empty
                    # too long, cut it into multiple lines
                    if len(line) > sj.cache[f"tb_ex_{mode}_max_per_line"]:
                        # split the line into multiple lines with the max length of the line set by the user
                        line = [
                            line[i:i + sj.cache[f"tb_ex_{mode}_max_per_line"]]
                            for i in range(0, len(line), sj.cache["tb_mw_tc_max_per_line"])
                        ]
                        # loop through the new lines
                        for newLine in line:
                            if newLine != "":  # not empty
                                # insert the new line
                                textToAppend += newLine + separator
                    else:
                        # if the line is not too long, insert it
                        textToAppend += line + separator
        else:
            textToAppend += separator

        ex.lbl_text.configure(text=textToAppend)
        ex.check_height_resize()

    def get_mw_tc(self) -> str:
        assert self.mw is not None
        return self.mw.tb_transcribed.get("1.0", "end")

    def get_mw_tl(self) -> str:
        assert self.mw is not None
        return self.mw.tb_translated.get("1.0", "end")

    def get_ex_tc(self) -> str:
        assert self.ex_tcw is not None
        return self.ex_tcw.lbl_text.cget("text")

    def get_ex_tl(self) -> str:
        assert self.ex_tlw is not None
        return self.ex_tlw.lbl_text.cget("text")

    def clear_mw_tc(self):
        assert self.mw is not None
        self.mw.tb_transcribed.delete("1.0", "end")

    def clear_mw_tl(self):
        assert self.mw is not None
        self.mw.tb_translated.delete("1.0", "end")

    def clear_ex_tc(self):
        assert self.ex_tcw is not None
        self.ex_tcw.lbl_text.configure(text=SUBTITLE_PLACEHOLDER)

    def clear_ex_tl(self):
        assert self.ex_tlw is not None
        self.ex_tlw.lbl_text.configure(text=SUBTITLE_PLACEHOLDER)


# ------------------ #
gc: GlobalClass = GlobalClass()
