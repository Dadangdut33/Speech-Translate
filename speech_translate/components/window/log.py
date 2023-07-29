import os
import threading
import time
import tkinter as tk
from tkinter import ttk

from speech_translate.components.custom.message import mbox
from speech_translate._path import app_icon
from speech_translate._contants import APP_NAME
from speech_translate.globals import gc, sj
from speech_translate.custom_logging import logger, current_log, dir_log, init_logging
from speech_translate.utils.helper import startFile, tb_copy_only


# Classes
class LogWindow:
    """Logger but shown in toplevel window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        self.root = tk.Toplevel(master)
        self.root.title(APP_NAME + " | Log")
        self.root.geometry("900x350")
        self.root.wm_withdraw()
        self.currentFontSize = 10
        self.isOpen = False
        self.stay_on_top = False
        self.thread_refresh = None
        gc.lw = self 

        # Frames
        self.f_1 = ttk.Frame(self.root)
        self.f_1.pack(side="top", fill="both", padx=5, pady=5, expand=True)

        self.f_bot = ttk.Frame(self.root)
        self.f_bot.pack(side="bottom", fill="both", expand=False)

        # Scrollbar
        self.sbY = ttk.Scrollbar(self.f_1, orient=tk.VERTICAL)
        self.sbY.pack(side="right", fill="both")

        self.tbLogger = tk.Text(self.f_1, height=5, width=100, font=("Consolas", self.currentFontSize))
        self.tbLogger.bind("<Key>", lambda event: tb_copy_only(event))  # Disable textbox input
        self.tbLogger.pack(side="left", fill="both", expand=True)
        self.tbLogger.configure(yscrollcommand=self.sbY.set)
        self.sbY.configure(command=self.tbLogger.yview)
        self.tbLogger.bind("<Control-MouseWheel>", lambda event: self.increase_font_size() if event.delta > 0 else self.lower_font_size())  # bind scrollwheel to change font size

        # Other stuff
        self.btn_clear = ttk.Button(self.f_bot, text="⚠ Clear", command=self.clearLog)
        self.btn_clear.pack(side="left", padx=5, pady=5)

        self.btn_refresh = ttk.Button(self.f_bot, text="🔄 Refresh", command=lambda: self.updateLog)
        self.btn_refresh.pack(side="left", padx=5, pady=5)

        self.btn_open_default_log = ttk.Button(self.f_bot, text="🗁 Open Log Folder", command=lambda: startFile(dir_log))
        self.btn_open_default_log.pack(side="left", padx=5, pady=5)

        self.cbtn_auto_scroll = ttk.Checkbutton(self.f_bot, text="Auto Scroll", command=lambda: sj.savePartialSetting("auto_scroll_log", self.cbtn_auto_scroll.instate(["selected"])), style="Switch.TCheckbutton")
        self.cbtn_auto_scroll.pack(side="left", padx=5, pady=5)

        self.cbtn_auto_refresh = ttk.Checkbutton(self.f_bot, text="Auto Refresh", command=lambda: sj.savePartialSetting("auto_refresh_log", self.cbtn_auto_refresh.instate(["selected"])), style="Switch.TCheckbutton")
        self.cbtn_auto_refresh.pack(side="left", padx=5, pady=5)

        self.cbtn_stay_on_top = ttk.Checkbutton(self.f_bot, text="Stay on Top", command=self.toggle_stay_on_top, style="Switch.TCheckbutton")
        self.cbtn_stay_on_top.pack(side="left", padx=5, pady=5)

        self.btn_close = ttk.Button(self.f_bot, text="Ok", command=self.on_closing, style="Accent.TButton")
        self.btn_close.pack(side="right", padx=5, pady=5)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.onInit()

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

    def onInit(self):
        if sj.cache["auto_scroll_log"]:
            self.cbtn_auto_scroll.invoke()
        else:
            self.cbtn_auto_scroll.invoke()
            self.cbtn_auto_scroll.invoke()

        if sj.cache["auto_refresh_log"]:
            self.cbtn_auto_refresh.invoke()
        else:
            self.cbtn_auto_refresh.invoke()
            self.cbtn_auto_refresh.invoke()

        # deselect stay on top
        self.cbtn_stay_on_top.invoke()
        self.cbtn_stay_on_top.invoke()

    # Show/Hide
    def show(self):
        self.root.after(0, self.after_show_called)

    def after_show_called(self):
        self.root.wm_deiconify()
        self.updateLog()
        self.isOpen = True
        self.start_refresh_thread()

    def on_closing(self):
        self.isOpen = False
        self.root.wm_withdraw()

    def toggle_stay_on_top(self):
        self.stay_on_top = not self.stay_on_top
        self.root.wm_attributes("-topmost", self.stay_on_top)

    def start_refresh_thread(self):
        self.thread_refresh = threading.Thread(target=self.update_periodically, daemon=True)
        self.thread_refresh.start()

    def update_periodically(self):
        while self.isOpen and sj.cache["auto_refresh_log"]:
            self.updateLog()

            time.sleep(1)

    def updateLog(self):
        prev_content = self.tbLogger.get(1.0, "end").strip()
        try:
            content = open(os.path.join(dir_log, current_log), encoding="utf-8").read().strip()
        except FileNotFoundError:
            logger.error(f"Log file not found | {os.path.join(dir_log, current_log)}")
            content = f"Log file not found | {os.path.join(dir_log, current_log)}"

        if len(prev_content) != len(content):
            if sj.cache["auto_scroll_log"]:
                self.tbLogger.delete(1.0, "end")
                self.tbLogger.insert("end", content)
                self.tbLogger.see("end")  # scroll to the bottom
            else:
                pos = self.sbY.get()
                self.tbLogger.delete(1.0, "end")
                self.tbLogger.insert("end", content)
                self.tbLogger.yview_moveto(pos[0])

    def clearLog(self):
        # Ask for confirmation first
        if mbox("Confirmation", "Are you sure you want to clear the log?", 3, self.root):
            init_logging()
            logger.info("Log cleared")
            self.updateLog()

    def lower_font_size(self):
        logger.info("Lowering font size")
        self.currentFontSize -= 1
        if self.currentFontSize < 3:
            self.currentFontSize = 3
        self.tbLogger.configure(font=("Consolas", self.currentFontSize))

    def increase_font_size(self):
        logger.info("Increasing font size")
        self.currentFontSize += 1
        if self.currentFontSize > 20:
            self.currentFontSize = 20
        self.tbLogger.configure(font=("Consolas", self.currentFontSize))
