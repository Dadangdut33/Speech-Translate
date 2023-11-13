import os
import copy
from ast import literal_eval
from platform import system
from shlex import quote
from threading import Lock, Thread
from tkinter import ttk
from PIL import ImageTk
from typing import TYPE_CHECKING, List, Literal, Optional, Sequence, Union

from stable_whisper import WhisperResult
from arabic_reshaper import reshape
from bidi.algorithm import get_display

from speech_translate.utils.types import ToInsert
from speech_translate.utils.helper import generate_color, html_to_separator, wrap_result
from ._path import dir_debug, dir_export, dir_log, dir_temp, dir_user
from .utils.setting import SettingJson

if system() == "Windows":
    from multiprocessing import Queue
    import pyaudiowpatch as pyaudio
else:
    # to get qsize on platform other than windows
    from .utils.custom.queue import MyQueue as Queue
    import pyaudio  # type: ignore

# Forward declaration for type hinting
if TYPE_CHECKING:
    from .ui.window.about import AboutWindow
    from .ui.window.log import LogWindow
    from .ui.window.main import AppTray, MainWindow
    from .ui.window.setting import SettingWindow
    from .ui.window.transcribed import TcsWindow
    from .ui.window.translated import TlsWindow

# ------------------ #
sj: SettingJson = SettingJson(os.path.join(dir_user, "setting.json"), dir_user, [dir_temp, dir_log, dir_export, dir_debug])


class BridgeClass:
    """
    Class containing all the static variables for the UI. It also contains some methods for the stuff to works.

    Stored like this in order to allow other file to use the same thing without circular import error.
    """
    def __init__(self):
        self.cuda: str = ""
        self.running_after_id: str = ""
        self.has_ffmpeg: bool = False

        # Flags
        self.running: bool = True
        self.recording: bool = False
        self.file_processing: bool = False
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

        # stream / transcribe
        self.stream: Optional[pyaudio.Stream] = None
        self.data_queue = Queue()
        self.current_rec_status: str = ""
        self.auto_detected_lang: str = "~"
        self.tc_lock: Optional[Lock] = None
        self.tc_sentences: List[Union[WhisperResult, str]] = []
        self.tl_sentences: List[Union[WhisperResult, str]] = []

        # file process
        self.file_tced_counter: int = 0
        self.file_tled_counter: int = 0
        self.mod_file_counter: int = 0

        # photoimage
        self.help_emoji: Union[ImageTk.PhotoImage, str] = ""
        self.wrench_emoji: Union[ImageTk.PhotoImage, str] = ""
        self.folder_emoji: Union[ImageTk.PhotoImage, str] = ""
        self.file_emoji: Union[ImageTk.PhotoImage, str] = ""
        self.open_emoji: Union[ImageTk.PhotoImage, str] = ""
        self.trash_emoji: Union[ImageTk.PhotoImage, str] = ""
        self.reset_emoji: Union[ImageTk.PhotoImage, str] = ""
        self.question_emoji: Union[ImageTk.PhotoImage, str] = ""

    def enable_rec(self):
        self.recording = True

    def disable_rec(self):
        self.recording = False

    def enable_file_process(self):
        self.file_processing = True

    def disable_file_process(self):
        self.file_processing = False

    def enable_tc(self):
        self.transcribing = True

    def disable_tc(self):
        self.transcribing = False

    def enable_tl(self):
        self.translating = True

    def disable_tl(self):
        self.translating = False

    def parse_to_tb(self, text: str):
        """Do some preprocessing to the text before inserting it to the text box.
        
        It will do the following:
        - replace html back to normal text.
        - Parse arabic text to be displayed correctly in tkinter text box if enabled.
        Parameters
        ----------
        text : str
            Text to be parsed.
        
        Returns
        -------
        str
            Parsed text.
        """
        text = html_to_separator(text)
        if sj.cache["parse_arabic"]:
            return str(get_display(reshape(text)))

        return text

    def insert_to_mw(self, text: str, mode: Literal["tc", "tl"], separator: str):
        assert self.mw is not None
        if mode == "tc":
            self.mw.tb_transcribed.insert("end", text + separator)
        elif mode == "tl":
            self.mw.tb_translated.insert("end", text + separator)

    def update_result_display(
        self, total_len: int, res_with_conf: List[ToInsert], mode: Literal["mw_tc", "ex_tc", "mw_tl", "ex_tl"]
    ):
        """Update display of the result to the respective text box. 

        Parameters
        ----------
        total_len : int
            Total word length of the result.
        res_with_conf : List[ToInsert]
            List of result with confidence value.
        mode : Literal[&quot;mw_tc&quot;, &quot;ex_tc&quot;, &quot;mw_tl&quot;, &quot;ex_tl&quot;]
            Mode to determine which text box to update.
        """
        # we access setting using .get here to remove pylance warning "LiteralString" is not a string literal
        # the 0 for second argument is just a placeholder
        # make deepcopy because we would modify the list
        copied_res = copy.deepcopy(res_with_conf)

        # if not infinite and text too long
        # remove words from the start based on how over the limit it is
        if sj.cache.get(f"tb_{mode}_limit_max") and total_len > sj.cache.get(f"tb_{mode}_max", 0):
            over_for = total_len - sj.cache.get(f"tb_{mode}_max")  # type: ignore
            index = 0

            while over_for > 0:
                # first get the sentence / word
                temp = copied_res[index]["text"]

                # get amount of characters to delete, while also decrementing the over_for
                delete_for = len(temp) if over_for > len(temp) else over_for
                over_for -= delete_for

                # now delete the characters in the sentence and reassign it to the list of sentences with confidence
                temp = temp[delete_for:]
                copied_res[index]["text"] = temp

                index += 1

        # # wrap result with the max length of the line set by the user
        if sj.cache.get(f"tb_{mode}_limit_max_per_line"):
            # Previously is_last is None, but now its either True or False
            # is last will determine the line break
            copied_res = wrap_result(copied_res, sj.cache.get(f"tb_{mode}_max_per_line", 0))

        # insert to each respective area
        # before inserting check some value:
        # if last, there will be a separator already so no need to add line break
        if "mw" in mode:
            assert self.mw is not None
            mw = self.mw.tb_transcribed if "tc" in mode else self.mw.tb_translated
            for res in copied_res:
                temp = res["text"] + "\n" if res["is_last"] is False else res["text"]
                if res["color"] is not None and {sj.cache.get(f"tb_{mode}_use_conf_color")}:
                    mw.insert_with_color(self.parse_to_tb(res["text"]), res["color"])
                else:
                    mw.insert("end", self.parse_to_tb(res["text"]))
        else:
            assert self.ex_tcw and self.ex_tlw is not None
            ex = self.ex_tcw.lbl_text if "tc" in mode else self.ex_tlw.lbl_text
            to_insert = ""
            for res in copied_res:
                temp = res["text"] + "<br />" if res["is_last"] is False else res["text"]
                color = res["color"] if {sj.cache.get(f"tb_{mode}_use_conf_color")
                                         } else sj.cache.get(f"tb_{mode}_font_color")
                if res["color"] is not None:
                    to_insert += f'''<span style="color: {color}">{temp}</span>'''
                else:
                    to_insert += f'''<span style="color: {sj.cache.get(f"tb_{mode}_font_color")}">{temp}</span>'''

            # Update the text
            ex.set_html(
                f'''<div style='font-family: {sj.cache.get(f"tb_{mode}_font")}; text-align: left; 
                font-size: {sj.cache.get(f"tb_{mode}_font_size")}px; 
                background-color: {sj.cache.get(f"tb_{mode}_bg_color")}; 
                font-weight: {"bold" if sj.cache.get(f"tb_{mode}_font_bold") else "normal"};'>
                        {to_insert}
                    </div>'''
            )

    def map_result_lists(self, source_list: Sequence[Union[WhisperResult, str]], store_list: List[ToInsert], separator: str):
        """
        Map List of whisper result according to user setting while also calculating its color based on the confidence value.
        
        Parameters
        ----------
        source_list : Sequence[Union[WhisperResult, str]]
            Source list to be mapped, can be either a list of whisper result or a list of string.
        store_list : List[ToInsert]
            List to store the mapped result.
        separator : str
            Separator to be added to the end of the result.

        Returns
        -------
        total_len : int
            Total word length of the mapped result.
        """
        total_len = 0
        low_color = sj.cache["gradient_low_conf"]
        high_color = sj.cache["gradient_high_conf"]
        for sentence in source_list:
            # if it's a string, confidence is None
            if isinstance(sentence, str):
                # already a full sentence, add separator directly
                sentence = sentence.strip() + separator
                total_len += len(sentence)
                store_list.append({"text": sentence, "color": None, "is_last": None})

            # colorization based on confidence per sentence, so get the confidence value from the segment
            elif sj.cache["colorize_per_segment"]:
                for segment in sentence.segments:
                    # lstrip if first only
                    temp = segment.text.lstrip() if segment.id == 0 else segment.text
                    confidence_total_word = 0
                    for word in segment.words:
                        confidence_total_word += word.probability

                    word_len = len(segment.words) if len(segment.words) != 0 else 1
                    confidence = confidence_total_word / word_len

                    store_list.append(
                        {
                            "text": temp,
                            "color": generate_color(confidence, low_color, high_color),
                            "is_last": None
                        }
                    )
                    total_len += len(temp)

                # add separator on the last group of segments in the sentence
                last_item = store_list[-1]
                last_item["text"] += separator

            # colorization based on confidence per word, so get the confidence value from the word
            elif sj.cache["colorize_per_word"]:
                for segment in sentence.segments:
                    for word in segment.words:
                        temp = word.word.lstrip() if word.id == 0 else word.word
                        store_list.append(
                            {
                                "text": temp,
                                "color": generate_color(word.probability, low_color, high_color),
                                "is_last": None
                            }
                        )
                        total_len += len(temp)

                # add separator on the last group of words from the segment in the sentence
                last_item = store_list[-1]
                last_item["text"] += separator

            # no colorization based on confidence. just append the sentence (the full sentence)
            else:
                # already a full sentence, add separator directly
                temp = sentence.text.strip() + separator
                total_len += len(sentence)
                store_list.append({"text": temp, "color": None, "is_last": None})

        return total_len

    def swap_textbox(self):
        """Swap the text box between the transcribed and translated"""
        assert self.mw is not None
        separator = literal_eval(quote(sj.cache["separate_with"]))
        self.tc_sentences, self.tl_sentences = self.tl_sentences, self.tc_sentences
        self.update_tc(None, separator)
        self.update_tl(None, separator)

    def update_tc(self, new_res: Union[WhisperResult, str, None], separator: str):
        """Update the transcribed text box with the new text.

        Parameters
        ----------
        new_res : Union[WhisperResult, str]
            New result to be added to the transcribed text box.
        separator : str
            Separator to be added to the end of the new result.
        """
        res_with_conf: List[ToInsert] = []
        total_len = self.map_result_lists(self.tc_sentences, res_with_conf, separator)
        if new_res is not None:
            total_len += self.map_result_lists([new_res], res_with_conf, separator)

        self.clear_mw_tc()
        self.clear_ex_tc()
        self.update_result_display(total_len, res_with_conf, "mw_tc")
        self.update_result_display(total_len, res_with_conf, "ex_tc")

    def update_tl(self, new_res: Union[WhisperResult, str, None], separator: str):
        """Update the translated text box with the new text.

        Parameters
        ----------
        new_res : Union[WhisperResult, str]
            New result to be added to the translated text box.
        separator : 
            Separator to be added to the end of the new result.
        """
        res_with_conf: List[ToInsert] = []
        total_len = self.map_result_lists(self.tl_sentences, res_with_conf, separator)
        if new_res is not None:
            total_len += self.map_result_lists([new_res], res_with_conf, separator)

        self.clear_mw_tl()
        self.clear_ex_tl()
        self.update_result_display(total_len, res_with_conf, "mw_tl")
        self.update_result_display(total_len, res_with_conf, "ex_tl")

    def clear_mw_tc(self):
        assert self.mw is not None
        self.mw.tb_transcribed.clear_text_and_tags()

    def clear_mw_tl(self):
        assert self.mw is not None
        self.mw.tb_translated.clear_text_and_tags()

    def clear_ex_tc(self):
        assert self.ex_tcw is not None
        self.ex_tcw.lbl_text.delete("1.0", "end")

    def clear_ex_tl(self):
        assert self.ex_tlw is not None
        self.ex_tlw.lbl_text.delete("1.0", "end")

    def clear_all(self):
        self.tc_sentences = []
        self.tl_sentences = []
        self.clear_mw_tc()
        self.clear_mw_tl()
        self.clear_ex_tc()
        self.clear_ex_tl()


# ------------------ #
bc = BridgeClass()
