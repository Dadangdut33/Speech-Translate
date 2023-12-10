from threading import Thread
from tkinter import Frame, Tk, Toplevel, font, ttk

from speech_translate._constants import APP_NAME
from speech_translate._path import p_app_icon
from speech_translate.linker import bc, sj
from speech_translate.ui.frame.setting.export import SettingExport
from speech_translate.ui.frame.setting.general import SettingGeneral
from speech_translate.ui.frame.setting.record import SettingRecord
from speech_translate.ui.frame.setting.textbox import SettingTextbox
from speech_translate.ui.frame.setting.transcribe import SettingTranscribe
from speech_translate.ui.frame.setting.translate import SettingTranslate
from speech_translate.utils.helper import bind_focus_recursively


class SettingWindow:
    """
    Setting UI
    """
    def __init__(self, master: Tk):
        # Flags
        bc.sw = self  # Add self to global class

        self.root = Toplevel(master)

        self.root.title(APP_NAME + " | Settings")
        self.root.geometry(sj.cache["sw_size"])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.minsize(600, 300)
        self.root.withdraw()

        self.fonts = list(font.families())
        self.fonts.append("TKDefaultFont")
        self.fonts.sort()

        # ------------------ Frames ------------------
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side="top", fill="x")

        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side="bottom", fill="x")

        # ------------------ Widgets ------------------
        # notebook
        self.tab_control = ttk.Notebook(self.frame_top)
        self.tab_control.pack(fill="both", expand=True)
        self.tab_control.bind("<<NotebookTabChanged>>", self.notebook_change)

        self.ft_general = ttk.Frame(self.tab_control)
        self.tab_control.add(self.ft_general, text="General")

        self.ft_record = ttk.Frame(self.tab_control)
        self.tab_control.add(self.ft_record, text="Device - Record")

        self.ft_transcribe = ttk.Frame(self.tab_control)
        self.tab_control.add(self.ft_transcribe, text="Whisper")

        self.ft_export = ttk.Frame(self.tab_control)
        self.tab_control.add(self.ft_export, text="File Export Result")

        self.ft_translate = ttk.Frame(self.tab_control)
        self.tab_control.add(self.ft_translate, text="Translate")

        self.ft_textbox = ttk.Frame(self.tab_control)
        self.tab_control.add(self.ft_textbox, text="Textbox")

        # Insert the frames
        self.f_general = SettingGeneral(self.root, self.ft_general)
        self.f_record = SettingRecord(self.root, self.ft_record)
        self.f_transcribe = SettingTranscribe(self.root, self.ft_transcribe)
        self.f_export = SettingExport(self.root, self.ft_export)
        self.f_translate = SettingTranslate(self.root, self.ft_translate)
        self.f_textbox = SettingTextbox(self.root, self.ft_textbox)

        # ------------------ Start ------------------
        self.__init_threaded()
        bind_focus_recursively(self.root, self.root)
        try:
            self.root.iconbitmap(p_app_icon)
        except Exception:
            pass

    # ------------------ Functions ------------------
    def __init_threaded(self):
        """
        Init some startup function in a thread to avoid blocking
        """
        Thread(target=self.f_general.delete_log_on_start, daemon=True).start()
        Thread(target=self.f_general.delete_temp_on_start, daemon=True).start()

    def save_win_size(self):
        """
        Save window size
        """
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w > 600 and h > 300:
            sj.save_key("sw_size", f"{w}x{h}")

    def on_close(self):
        Thread(target=self.f_record.call_both_with_wait, args=[False], daemon=True).start()
        self.save_win_size()
        self.root.withdraw()

    def show(self):
        self.root.deiconify()

        if not self.f_general.model_checked and sj.cache["auto_verify_model_on_first_setting_open"]:
            Thread(target=self.f_general.check_model_on_first_open, daemon=True).start()

        self.notebook_change()

    def notebook_change(self, _event=None):
        pos = self.tab_control.index(self.tab_control.select())
        if pos == 1:
            Thread(target=self.f_record.call_both_with_wait, daemon=True).start()
        else:
            Thread(target=self.f_record.call_both_with_wait, args=[False], daemon=True).start()
