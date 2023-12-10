from os import path
from threading import Thread
from time import sleep
from tkinter import Text, Tk, Toplevel, ttk

from loguru import logger

from speech_translate._constants import APP_NAME
from speech_translate._logging import clear_current_log_file, current_log
from speech_translate._path import dir_log, p_app_icon
from speech_translate.linker import bc, sj
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.message import mbox
from speech_translate.utils.helper import bind_focus_recursively, start_file, tb_copy_only


class LogWindow:
    """Logger but shown in toplevel window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: Tk):
        self.root = Toplevel(master)
        self.root.title(APP_NAME + " | Log")
        self.root.geometry("1200x350")
        self.root.minsize(600, 150)
        self.root.wm_withdraw()
        self.current_font_size = 10
        self.is_open = False
        self.stay_on_top = False
        self.thread_refresh = None
        bc.lw = self

        # Frames
        self.f_1 = ttk.Frame(self.root)
        self.f_1.pack(side="top", fill="both", padx=5, pady=5, expand=True)

        self.f_bot = ttk.Frame(self.root)
        self.f_bot.pack(side="bottom", fill="both", expand=False)

        # Scrollbar
        self.sb_y = ttk.Scrollbar(self.f_1, orient="vertical")
        self.sb_y.pack(side="right", fill="both")

        self.tb_logger = Text(self.f_1, height=5, width=100, font=("Consolas", self.current_font_size))
        self.tb_logger.bind("<Key>", tb_copy_only)  # Disable textbox input
        self.tb_logger.pack(side="left", fill="both", expand=True)
        self.tb_logger.configure(yscrollcommand=self.sb_y.set)
        self.sb_y.configure(command=self.tb_logger.yview)
        self.tb_logger.bind(
            "<Control-MouseWheel>", lambda event: self.increase_font_size() if event.delta > 0 else self.lower_font_size()
        )  # bind scrollwheel to change font size

        # Other stuff
        self.btn_clear = ttk.Button(self.f_bot, text="⚠ Clear", command=self.clear_log)
        self.btn_clear.pack(side="left", padx=5, pady=5)

        self.btn_refresh = ttk.Button(self.f_bot, text="🔄 Refresh", command=lambda: self.update_log)
        self.btn_refresh.pack(side="left", padx=5, pady=5)

        self.btn_open_default_log = ttk.Button(self.f_bot, text="🗁 Open Log Folder", command=lambda: start_file(dir_log))
        self.btn_open_default_log.pack(side="left", padx=5, pady=5)

        self.cbtn_auto_scroll = CustomCheckButton(
            self.f_bot,
            sj.cache["auto_scroll_log"],
            lambda x: sj.save_key("auto_scroll_log", x),
            text="Auto Scroll",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_scroll.pack(side="left", padx=5, pady=5)

        self.cbtn_auto_refresh = CustomCheckButton(
            self.f_bot,
            sj.cache["auto_refresh_log"],
            lambda x: sj.save_key("auto_refresh_log", x),
            text="Auto Refresh",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_refresh.pack(side="left", padx=5, pady=5)

        self.cbtn_stay_on_top = CustomCheckButton(
            self.f_bot, False, text="Stay on Top", style="Switch.TCheckbutton", command=self.toggle_stay_on_top
        )
        self.cbtn_stay_on_top.pack(side="left", padx=5, pady=5)

        self.btn_close = ttk.Button(self.f_bot, text="Ok", command=self.on_closing, style="Accent.TButton")
        self.btn_close.pack(side="right", padx=5, pady=5)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        bind_focus_recursively(self.root, self.root)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(p_app_icon)
        except Exception:
            pass

    # Show/Hide
    def show(self):
        self.root.after(0, self.after_show_called)

    def after_show_called(self):
        self.root.wm_deiconify()
        self.update_log()
        self.is_open = True
        self.start_refresh_thread()

    def on_closing(self):
        self.is_open = False
        self.root.wm_withdraw()

    def toggle_stay_on_top(self):
        self.stay_on_top = not self.stay_on_top
        self.root.wm_attributes("-topmost", self.stay_on_top)

    def start_refresh_thread(self):
        self.thread_refresh = Thread(target=self.update_periodically, daemon=True)
        self.thread_refresh.start()

    def update_periodically(self):
        while self.is_open and sj.cache["auto_refresh_log"]:
            self.update_log()

            sleep(1)

    def update_log(self):
        prev_content = self.tb_logger.get(1.0, "end").strip()
        try:
            content = open(path.join(dir_log, current_log), encoding="utf-8").read().strip()
        except FileNotFoundError:
            logger.error(f"Log file not found | {path.join(dir_log, current_log)}")
            content = f"Log file not found | {path.join(dir_log, current_log)}"

        if len(prev_content) != len(content):
            if sj.cache["auto_scroll_log"]:
                self.tb_logger.delete(1.0, "end")
                self.tb_logger.insert("end", content)
                self.tb_logger.see("end")  # scroll to the bottom
            else:
                pos = self.sb_y.get()
                self.tb_logger.delete(1.0, "end")
                self.tb_logger.insert("end", content)
                self.tb_logger.yview_moveto(pos[0])

    def clear_log(self):
        # Ask for confirmation first
        if mbox("Confirmation", "Are you sure you want to clear the log?", 3, self.root):
            clear_current_log_file()
            logger.info("Log cleared")
            self.update_log()

    def lower_font_size(self):
        logger.info("Lowering font size")
        self.current_font_size -= 1
        self.current_font_size = max(self.current_font_size, 3)
        self.tb_logger.configure(font=("Consolas", self.current_font_size))

    def increase_font_size(self):
        logger.info("Increasing font size")
        self.current_font_size += 1
        self.current_font_size = min(self.current_font_size, 20)
        self.tb_logger.configure(font=("Consolas", self.current_font_size))
