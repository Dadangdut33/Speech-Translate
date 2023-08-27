import os
import time
import platform
import threading
import tkinter as tk
import torch
import signal  # Import the signal module to handle Ctrl+C
from tkinter import ttk, filedialog
from typing import Literal, Dict

from PIL import Image, ImageDraw
from pystray import Icon as icon
from pystray import Menu as menu
from pystray import MenuItem as item

from speech_translate._version import __version__
from speech_translate._path import app_icon
from speech_translate._contants import APP_NAME
from speech_translate.globals import sj, gc
from speech_translate.custom_logging import logger

from speech_translate.components.custom.message import mbox
from speech_translate.components.custom.tooltip import tk_tooltip

from speech_translate.components.window.about import AboutWindow
from speech_translate.components.window.log import LogWindow
from speech_translate.components.window.setting import SettingWindow
from speech_translate.components.window.transcribed import TcsWindow
from speech_translate.components.window.translated import TlsWindow

from speech_translate.utils.model_download import verify_model, download_model
from speech_translate.utils.helper import cbtn_invoker, emoji_img, tb_copy_only, nativeNotify, popup_menu, windows_os_only
from speech_translate.utils.style import set_ui_style, init_theme, get_theme_list, get_current_theme
from speech_translate.utils.helper import up_first_case, start_file
from speech_translate.utils.helper_whisper import append_dot_en, modelKeys, modelSelectDict
from speech_translate.utils.language import engine_select_source_dict, engine_select_target_dict, whisper_compatible
from speech_translate.utils.record import (
    get_input_devices,
    get_output_devices,
    get_host_apis,
    get_default_output_device,
    get_default_input_device,
    get_default_host_api,
    file_input,
    record_realtime,
)

# Terminal window hide/showing
try:
    if platform.system() != "Windows":
        raise Exception("Console window is not hidden automatically because Not running on Windows")

    import ctypes
    import win32.lib.win32con as win32con
    import win32gui

    kernel32 = ctypes.WinDLL("kernel32")
    user32 = ctypes.WinDLL("user32")

    hWnd = kernel32.GetConsoleWindow()
    win32gui.ShowWindow(hWnd, win32con.SW_HIDE)
    logger.info(
        "Console window hidden. If it is not hidden (only minimized), try changing your default windows terminal to windows cmd."
    )
    gc.cw = hWnd
except Exception as e:
    logger.debug("Ignore this error if not running on Windows OR if not run directly from terminal (e.g. run from IDE)")
    logger.exception(e)
    pass


# Function to handle Ctrl+C and exit just like clicking the exit button
def signal_handler(sig, frame):
    logger.info("Received Ctrl+C, exiting...")
    gc.running = False


signal.signal(signal.SIGINT, signal_handler)  # Register the signal handler for Ctrl+C


class AppTray:
    """
    Tray app
    """

    def __init__(self):
        self.icon: icon = None  # type: ignore
        self.menu: menu = None  # type: ignore
        self.menu_items = None  # type: ignore
        gc.tray = self
        self.create_tray()
        logger.info("Tray created")

    # -- Tray icon
    def create_image(self, width, height, color1, color2):
        # Generate an image and draw a pattern
        image = Image.new("RGB", (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
        dc.rectangle((0, height // 2, width // 2, height), fill=color2)

        return image

    # -- Create tray
    def create_tray(self):
        try:
            trayIco = Image.open(app_icon)
        except Exception:
            trayIco = self.create_image(64, 64, "black", "white")

        self.menu_items = (
            item(f"{APP_NAME} {__version__}", lambda *args: None, enabled=False),  # do nothing
            menu.SEPARATOR,
            item("About", self.open_about),
            item("Settings", self.open_setting),
            item("Show Main Window", self.open_app),
            menu.SEPARATOR,
            item("Exit", self.exit_app),
            item("Hidden onclick", self.open_app, default=True, visible=False),  # onclick the icon will open_app
        )
        self.menu = menu(*self.menu_items)
        self.icon = icon("Speech Translate", trayIco, f"Speech Translate V{__version__}", self.menu)
        self.icon.run_detached()

    # -- Open app
    def open_app(self):
        assert gc.mw is not None  # Show main window
        gc.mw.show_window()

    # -- Open setting window
    def open_setting(self):
        assert gc.sw is not None
        gc.sw.show()

    # -- Open about window
    def open_about(self):
        assert gc.about is not None
        gc.about.show()

    # -- Exit app by flagging runing false to stop main loop
    def exit_app(self):
        gc.running = False


class MainWindow:
    """
    Main window of the app
    """

    def __init__(self):
        # ------------------ Window ------------------
        # UI
        self.root = tk.Tk()
        self.wrench_emoji = emoji_img(16, "     🛠️")
        gc.cuda = check_cuda_and_gpu()

        self.root.title(APP_NAME)
        self.root.geometry(sj.cache["mw_size"])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.wm_attributes("-topmost", False)  # Default False

        # Flags
        self.always_on_top: bool = False
        self.notified_hidden: bool = False
        self.console_opened: bool = False
        gc.mw = self

        # Styles
        self.style = ttk.Style()
        gc.style = self.style

        init_theme()
        gc.native_theme = get_current_theme()  # get first theme before changing
        gc.theme_lists = list(get_theme_list())

        # rearrange some positions
        try:
            gc.theme_lists.remove("sv")
        except Exception:  # sv theme is not available
            gc.theme_lists.remove("sun-valley-dark")
            gc.theme_lists.remove("sun-valley-light")

        gc.theme_lists.remove(gc.native_theme)  # remove native theme from list
        gc.theme_lists.insert(0, gc.native_theme)  # add native theme to top of list
        logger.debug(f"Available Theme to use: {gc.theme_lists}")
        gc.theme_lists.insert(len(gc.theme_lists), "custom")

        set_ui_style(sj.cache["theme"])

        # ------------------ Frames ------------------
        self.f1_toolbar = ttk.Frame(self.root)
        self.f1_toolbar.pack(side="top", fill="x", expand=False, pady=(5, 0))
        self.f1_toolbar.bind("<Button-1>", lambda event: self.root.focus_set())

        self.f2_textBox = ttk.Frame(self.root)
        self.f2_textBox.pack(side="top", fill="both", expand=True)
        self.f2_textBox.bind("<Button-1>", lambda event: self.root.focus_set())

        self.f3_toolbar = ttk.Frame(self.root)
        self.f3_toolbar.pack(side="top", fill="x", expand=False)
        self.f3_toolbar.bind("<Button-1>", lambda event: self.root.focus_set())

        self.f4_statusbar = ttk.Frame(self.root)
        self.f4_statusbar.pack(side="bottom", fill="x", expand=False)
        self.f4_statusbar.bind("<Button-1>", lambda event: self.root.focus_set())

        # ------------------ Elements ------------------
        # -- f1_toolbar
        # model
        self.lbl_model = ttk.Label(self.f1_toolbar, text="Model:")
        self.lbl_model.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        self.cb_model = ttk.Combobox(self.f1_toolbar, values=modelKeys, state="readonly")
        self.cb_model.pack(side="left", fill="x", padx=5, pady=5, expand=False)
        tk_tooltip(
            self.cb_model,
            """Model size, larger models are more accurate but slower and require more VRAM/CPU power. 
            \rIf you have a low end GPU, use Tiny or Base. Don't use large unless you really need it or have super computer because it's very slow.
            \rModel specs: \n- Tiny: ~1 GB Vram\n- Base: ~1 GB Vram\n- Small: ~2 GB Vram\n- Medium: ~5 GB Vram\n- Large: ~10 GB Vram""".strip(),
            wrapLength=400,
        )
        self.cb_model.bind("<<ComboboxSelected>>", lambda _: sj.save_key("model", modelSelectDict[self.cb_model.get()]))

        # engine
        self.lbl_engine = ttk.Label(self.f1_toolbar, text="Translate:")
        self.lbl_engine.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        self.cb_engine = ttk.Combobox(
            self.f1_toolbar, values=["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"], state="readonly"
        )
        self.cb_engine.pack(side="left", fill="x", padx=5, pady=5, expand=True)
        self.cb_engine.bind("<<ComboboxSelected>>", self.cb_engine_change)

        # from
        self.lbl_source = ttk.Label(self.f1_toolbar, text="From:")
        self.lbl_source.pack(side="left", padx=5, pady=5)

        self.cb_sourceLang = ttk.Combobox(
            self.f1_toolbar, values=engine_select_source_dict["Whisper"], state="readonly"
        )  # initial value
        self.cb_sourceLang.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.cb_sourceLang.bind("<<ComboboxSelected>>", lambda _: sj.save_key("sourceLang", self.cb_sourceLang.get()))

        # to
        self.lbl_to = ttk.Label(self.f1_toolbar, text="To:")
        self.lbl_to.pack(side="left", padx=5, pady=5)

        self.cb_targetLang = ttk.Combobox(
            self.f1_toolbar, values=[up_first_case(x) for x in whisper_compatible], state="readonly"
        )  # initial value
        self.cb_targetLang.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.cb_targetLang.bind("<<ComboboxSelected>>", lambda _: sj.save_key("targetLang", self.cb_targetLang.get()))

        # swap
        self.btn_swap = ttk.Button(self.f1_toolbar, text="Swap", command=self.cb_swap_lang)
        self.btn_swap.pack(side="left", padx=5, pady=5)

        # clear
        self.btn_clear = ttk.Button(self.f1_toolbar, text="Clear", command=self.tb_clear, style="Accent.TButton")
        self.btn_clear.pack(side="left", padx=5, pady=5)

        # -- f2_textBox
        self.tb_transcribed_bg = tk.Frame(self.f2_textBox, bg="#7E7E7E")
        self.tb_transcribed_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.sb_transcribed = ttk.Scrollbar(self.tb_transcribed_bg)
        self.sb_transcribed.pack(side="right", fill="y")

        self.tb_transcribed = tk.Text(
            self.tb_transcribed_bg,
            height=5,
            width=25,
            relief="flat",
            font=(sj.cache["tb_mw_tc_font"], sj.cache["tb_mw_tc_font_size"]),
        )
        self.tb_transcribed.bind("<Key>", tb_copy_only)
        self.tb_transcribed.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self.tb_transcribed.configure(yscrollcommand=self.sb_transcribed.set)
        self.sb_transcribed.configure(command=self.tb_transcribed.yview)

        self.tb_translated_bg = tk.Frame(self.f2_textBox, bg="#7E7E7E")
        self.tb_translated_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.sb_translated = ttk.Scrollbar(self.tb_translated_bg)
        self.sb_translated.pack(side="right", fill="y")

        self.tb_translated = tk.Text(
            self.tb_translated_bg,
            height=5,
            width=25,
            relief="flat",
            font=(sj.cache["tb_mw_tl_font"], sj.cache["tb_mw_tl_font_size"]),
        )
        self.tb_translated.bind("<Key>", tb_copy_only)
        self.tb_translated.pack(fill="both", expand=True, padx=1, pady=1)
        self.tb_translated.configure(yscrollcommand=self.sb_translated.set)
        self.sb_translated.configure(command=self.tb_translated.yview)

        # -- f3_toolbar
        self.f3_1 = ttk.Frame(self.f3_toolbar)
        self.f3_1.pack(side="left", fill="x", expand=True)
        self.f3_1.bind("<Button-1>", lambda event: self.root.focus_set())

        self.f3_1_row1 = ttk.Frame(self.f3_1)
        self.f3_1_row1.pack(side="top", fill="x")
        self.f3_1_row1.bind("<Button-1>", lambda event: self.root.focus_set())

        self.f3_1_row2 = ttk.Frame(self.f3_1)
        self.f3_1_row2.pack(side="top", fill="x")
        self.f3_1_row2.bind("<Button-1>", lambda event: self.root.focus_set())

        self.f3_1_row3 = ttk.Frame(self.f3_1)
        self.f3_1_row3.pack(side="top", fill="x")
        self.f3_1_row3.bind("<Button-1>", lambda event: self.root.focus_set())

        # -- hostAPI
        self.lbl_hostAPI = ttk.Label(self.f3_1_row1, text="HostAPI:", font="TkDefaultFont 9 bold", width=10)
        self.lbl_hostAPI.pack(side="left", padx=5, pady=0, ipady=0)
        tk_tooltip(
            self.lbl_hostAPI,
            "HostAPI for the input device. There are many hostAPI for your device and it is recommended to follow the default value, other than that it might not work or crash the app.",
            wrapLength=350,
        )

        self.cb_hostAPI = ttk.Combobox(self.f3_1_row1, values=[], state="readonly")
        self.cb_hostAPI.bind(
            "<<ComboboxSelected>>", lambda _: sj.save_key("hostAPI", self.cb_hostAPI.get()) or self.hostAPI_change()
        )
        self.cb_hostAPI.pack(side="left", padx=5, pady=0, ipady=0, expand=True, fill="x")

        self.btn_config_hostAPI = ttk.Button(
            self.f3_1_row1,
            image=self.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_hostAPI),
        )
        self.btn_config_hostAPI.pack(side="left", padx=5, pady=0, ipady=0)
        self.menu_hostAPI = self.input_device_menu("hostAPI")

        # -- mic
        self.lbl_mic = ttk.Label(self.f3_1_row2, text="Microphone:", font="TkDefaultFont 9 bold", width=10)
        self.lbl_mic.pack(side="left", padx=5, pady=0, ipady=0)
        tk_tooltip(self.lbl_mic, "Microphone for the input device.")

        self.cb_mic = ttk.Combobox(self.f3_1_row2, values=[], state="readonly")
        self.cb_mic.bind("<<ComboboxSelected>>", lambda _: sj.save_key("mic", self.cb_mic.get()))
        self.cb_mic.pack(side="left", padx=5, pady=0, ipady=0, expand=True, fill="x")

        self.btn_config_mic = ttk.Button(
            self.f3_1_row2,
            image=self.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_mic),
        )
        self.btn_config_mic.pack(side="left", padx=5, pady=0, ipady=0)

        self.menu_mic = self.input_device_menu("mic")

        # -- speaker
        self.lbl_speaker = ttk.Label(self.f3_1_row3, text="Speaker:", font="TkDefaultFont 9 bold", width=10)
        self.lbl_speaker.pack(side="left", padx=5, pady=0, ipady=0)
        tk_tooltip(self.lbl_speaker, "Speaker to record the system audio")

        self.cb_speaker = ttk.Combobox(self.f3_1_row3, values=[], state="readonly")
        self.cb_speaker.bind("<<ComboboxSelected>>", lambda _: sj.save_key("speaker", self.cb_speaker.get()))
        self.cb_speaker.pack(side="left", padx=5, pady=0, ipady=0, expand=True, fill="x")

        self.btn_config_speaker = ttk.Button(
            self.f3_1_row3,
            image=self.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_speaker),
        )
        self.btn_config_speaker.pack(side="left", padx=5, pady=0, ipady=0)

        self.menu_speaker = self.input_device_menu("speaker")

        # -- separator
        self.sep_btn_f3R1 = ttk.Separator(self.f3_1_row1, orient="vertical")
        self.sep_btn_f3R1.pack(side="left", fill="y", pady=0, ipady=0)

        self.sep_btn_f3R2 = ttk.Separator(self.f3_1_row2, orient="vertical")
        self.sep_btn_f3R2.pack(side="left", fill="y", pady=0, ipady=0)

        self.sep_btn_f3R3 = ttk.Separator(self.f3_1_row3, orient="vertical")
        self.sep_btn_f3R3.pack(side="left", fill="y", pady=0, ipady=0)

        # ------
        self.f3_2 = ttk.Frame(self.f3_toolbar)
        self.f3_2.pack(side="left", fill="x")

        self.f3_2_row1 = ttk.Frame(self.f3_2)
        self.f3_2_row1.pack(side="top", fill="x")

        self.f3_2_row2 = ttk.Frame(self.f3_2)
        self.f3_2_row2.pack(side="top", fill="x")

        self.f3_2_row3 = ttk.Frame(self.f3_2)
        self.f3_2_row3.pack(side="top", fill="x")

        self.lbl_task = ttk.Label(self.f3_2_row1, text="Task:", font="TkDefaultFont 9 bold", width=10)
        self.lbl_task.pack(side="left", padx=5, pady=5, ipady=0)

        self.cbtn_task_transcribe = ttk.Checkbutton(
            self.f3_2_row2,
            text="Transcribe",
            width=10,
            command=lambda: self.mode_change() or sj.save_key("transcribe", "selected" in self.cbtn_task_transcribe.state()),
        )
        self.cbtn_task_transcribe.pack(side="left", padx=5, pady=2.5, ipady=0)

        self.cbtn_task_translate = ttk.Checkbutton(
            self.f3_2_row3,
            text="Translate",
            width=10,
            command=lambda: self.mode_change() or sj.save_key("translate", "selected" in self.cbtn_task_translate.state()),
        )
        self.cbtn_task_translate.pack(side="left", padx=5, pady=2.5, ipady=0)

        # ------
        self.f3_3 = ttk.Frame(self.f3_toolbar)
        self.f3_3.pack(side="left", fill="x")

        self.f3_3_row1 = ttk.Frame(self.f3_3)
        self.f3_3_row1.pack(side="top", fill="x")

        self.f3_3_row2 = ttk.Frame(self.f3_3)
        self.f3_3_row2.pack(side="top", fill="x")

        self.f3_3_row3 = ttk.Frame(self.f3_3)
        self.f3_3_row3.pack(side="top", fill="x")

        self.lbl_temp = ttk.Label(self.f3_3_row1, text="Input:", font="TkDefaultFont 9 bold", width=10)
        self.lbl_temp.pack(side="left", padx=5, pady=5, ipady=0)

        self.radio_mic = ttk.Radiobutton(
            self.f3_3_row2, text="Microphone", value="mic", width=12, command=lambda: sj.save_key("input", "mic")
        )
        self.radio_mic.pack(side="left", padx=5, pady=2.5, ipady=0)

        self.radio_speaker = ttk.Radiobutton(
            self.f3_3_row3,
            text="Speaker",
            value="speaker",
            width=12,
            command=lambda: sj.save_key("input", "speaker"),
        )
        self.radio_speaker.pack(side="left", padx=5, pady=2.5, ipady=0)

        # ------
        self.f3_4 = ttk.Frame(self.f3_toolbar)
        self.f3_4.pack(side="left", fill="x")

        self.f3_4_row1 = ttk.Frame(self.f3_4)
        self.f3_4_row1.pack(side="top", fill="x")

        self.f3_4_row2 = ttk.Frame(self.f3_4)
        self.f3_4_row2.pack(side="top", fill="x")

        self.btn_record = ttk.Button(self.f3_4_row1, text="Record", command=self.rec)
        self.btn_record.pack(side="right", padx=5, pady=5)
        tk_tooltip(self.btn_record, "Record sound from selected input device and process it according to set task")

        self.btn_import_file = ttk.Button(self.f3_4_row2, text="Import file", command=self.import_file)
        self.btn_import_file.pack(side="right", padx=5, pady=5)
        tk_tooltip(self.btn_import_file, "Transcribe/Translate from a file (video or audio)")

        # export button
        self.btn_copy = ttk.Button(self.f3_4_row1, text="Copy", command=lambda: popup_menu(self.root, self.menu_copy))
        self.btn_copy.pack(side="right", padx=5, pady=5)
        tk_tooltip(self.btn_copy, "Copy the text to clipboard", wrapLength=250)

        self.menu_copy = tk.Menu(self.root, tearoff=0)
        self.menu_copy.add_command(label="Copy transcribed text", command=lambda: self.copy_tb("transcribed"))
        self.menu_copy.add_command(label="Copy translated text", command=lambda: self.copy_tb("translated"))

        self.btn_export = ttk.Button(self.f3_4_row2, text="Export", command=self.export_result)
        self.btn_export.pack(side="right", padx=5, pady=5)
        tk_tooltip(
            self.btn_export,
            "Export results to a file (txt)\n\nFor srt export with timestamps please use import file.",
            wrapLength=250,
        )

        # -- f4_statusbar
        # load bar
        self.loadBar = ttk.Progressbar(self.f4_statusbar, orient="horizontal", length=100, mode="determinate")
        self.loadBar.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # ------------------ Menubar ------------------
        self.menubar = tk.Menu(self.root)
        self.fm_file = tk.Menu(self.menubar, tearoff=0)
        self.fm_file.add_checkbutton(label="Stay on top", command=self.toggle_always_on_top)
        self.fm_file.add_separator()
        self.fm_file.add_command(label="Hide", command=lambda: self.root.withdraw())
        self.fm_file.add_command(label="Exit", command=self.quit_app)
        self.menubar.add_cascade(label="File", menu=self.fm_file)

        self.fm_view = tk.Menu(self.menubar, tearoff=0)
        self.fm_view.add_command(label="Settings", command=self.open_setting, accelerator="F2")
        self.fm_view.add_command(label="Log", command=self.open_log)
        if platform.system() == "Windows":
            self.fm_view.add_checkbutton(label="Console/Terminal", command=self.toggle_console)
        self.menubar.add_cascade(label="View", menu=self.fm_view)

        self.fm_generate = tk.Menu(self.menubar, tearoff=0)
        self.fm_generate.add_command(
            label="Transcribed Speech Subtitle Window", command=self.open_detached_tcw, accelerator="F3"
        )
        self.fm_generate.add_command(
            label="Translated Speech Subtitle Window", command=self.open_detached_tlw, accelerator="F4"
        )
        self.menubar.add_cascade(label="Generate", menu=self.fm_generate)

        self.fm_help = tk.Menu(self.menubar, tearoff=0)
        self.fm_help.add_command(label="About", command=self.open_about, accelerator="F1")
        self.menubar.add_cascade(label="Help", menu=self.fm_help)

        self.root.configure(menu=self.menubar)

        # ------------------ Bind keys ------------------
        self.root.bind("<F1>", self.open_about)
        self.root.bind("<F2>", self.open_setting)
        self.root.bind("<F3>", self.open_detached_tcw)
        self.root.bind("<F4>", self.open_detached_tlw)

        # ------------------ on Start ------------------
        # Start polling
        gc.running_after_id = self.root.after(1000, self.is_running_poll)
        self.onInit()

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

    # ------------------ Handle window ------------------
    def save_win_size(self):
        """
        Save window size
        """
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w > 600 and h > 300:
            sj.save_key("mw_size", f"{w}x{h}")

    def cleanup(self):
        # cancel the is_running_poll
        self.root.after_cancel(gc.running_after_id)

        gc.disableRecording()
        gc.disableTranscribing()
        gc.disableTranslating()

        logger.info("Stopping tray...")
        if gc.tray:
            gc.tray.icon.stop()

        # destroy windows
        logger.info("Destroying windows...")
        gc.sw.root.destroy()  # type: ignore
        gc.about.root.destroy()  # type: ignore
        gc.ex_tcw.root.destroy()  # type: ignore
        gc.ex_tlw.root.destroy()  # type: ignore
        self.root.destroy()

        if gc.dl_thread and gc.dl_thread.is_alive():
            logger.info("Killing download process...")
            gc.cancel_dl = True

    # Quit the app
    def quit_app(self):
        # save window size
        self.save_win_size()
        gc.sw.save_win_size()  # type: ignore

        if platform.system() == "Windows":
            try:
                if gc.cw:
                    win32gui.ShowWindow(gc.cw, win32con.SW_SHOW)
            except:
                pass

        self.cleanup()
        logger.info("Exiting...")
        try:
            os._exit(0)
        except SystemExit:
            logger.info("Exit successful")

    def restart_app(self):
        if gc.transcribing or gc.translating or gc.recording or (gc.dl_thread and gc.dl_thread.is_alive()):
            # prompt
            if not mbox(
                "Restarting app...",
                "There is a process still running, are you sure you want to restart the app?\n\nThis will stop the process and may cause data loss!",
                3,
            ):
                return

        # save window size
        self.save_win_size()
        gc.sw.save_win_size()  # type: ignore

        self.cleanup()
        logger.info("Restarting...")  # restart
        main()

    # Show window
    def show_window(self):
        self.root.after(0, self.root.deiconify)

    # Close window
    def on_close(self):
        self.save_win_size()

        # Only show notification once
        if not self.notified_hidden and not sj.cache["supress_hidden_to_tray"]:
            nativeNotify("Hidden to tray", "The app is still running in the background.")
            self.notified_hidden = True

        self.root.withdraw()

    # check if the app is running or not, to close the app from tray
    def is_running_poll(self):
        if not gc.running:
            self.quit_app()

        gc.running_after_id = self.root.after(1000, self.is_running_poll)

    # Toggle Stay on top
    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.root.wm_attributes("-topmost", self.always_on_top)

    # ------------------ Open External Window ------------------
    def open_about(self, _event=None):
        assert gc.about is not None
        gc.about.show()

    def open_setting(self, _event=None):
        assert gc.sw is not None
        gc.sw.show()

    def open_log(self, _event=None):
        assert gc.lw is not None
        gc.lw.show()

    def toggle_console(self):
        if platform.system() != "Windows":
            logger.info("Console toggling is only available on Windows")
            return

        if not self.console_opened:
            win32gui.ShowWindow(gc.cw, win32con.SW_SHOW)
        else:
            win32gui.ShowWindow(gc.cw, win32con.SW_HIDE)

        self.console_opened = not self.console_opened
        logger.debug(f"Console toggled, now {'opened' if self.console_opened else 'closed'}")

    def open_detached_tcw(self, _event=None):
        assert gc.ex_tcw is not None
        gc.ex_tcw.show()

    def open_detached_tlw(self, _event=None):
        assert gc.ex_tlw is not None
        gc.ex_tlw.show()

    # ------------------ Functions ------------------
    # error
    def errorNotif(self, err: str):
        nativeNotify("Unexpected Error!", err)

    def copy_tb(self, theType: Literal["transcribed", "translated"]):
        tb_dict = {"transcribed": self.tb_transcribed, "translated": self.tb_translated}

        self.root.clipboard_clear()
        self.root.clipboard_append(tb_dict[theType].get("1.0", "end"))
        self.root.update()

        self.btn_copy.configure(text="Copied!")

        # reset after 1 second
        self.root.after(1000, lambda: self.btn_copy.configure(text="Copy"))

    # on start
    def onInit(self):
        self.cb_model.set({v: k for k, v in modelSelectDict.items()}[sj.cache["model"]])
        self.cb_sourceLang.set(sj.cache["sourceLang"])
        self.cb_targetLang.set(sj.cache["targetLang"])
        self.cb_engine.set(sj.cache["tl_engine"])
        cbtn_invoker(sj.cache["transcribe"], self.cbtn_task_transcribe)
        cbtn_invoker(sj.cache["translate"], self.cbtn_task_translate)
        if sj.cache["input"] == "mic":
            cbtn_invoker(True, self.radio_mic)
        elif sj.cache["input"] == "speaker":
            cbtn_invoker(True, self.radio_speaker)

        if platform.system() != "Windows":
            self.radio_speaker.configure(state="disabled")

        # update on start
        self.cb_engine_change()
        self.mode_change()
        self.cb_input_device_init()

        windows_os_only([self.radio_speaker, self.cb_speaker, self.lbl_speaker, self.btn_config_speaker])

    # mic
    def cb_input_device_init(self):
        """
        Initialize input device combobox

        Will check previous options and set to default if not available.
        If default is not available, will show a warning.
        """
        success, host_detail = get_default_host_api()
        if success:
            assert isinstance(host_detail, Dict)
            defaultHost = str(host_detail["name"])
        else:
            defaultHost = ""

        self.cb_hostAPI["values"] = get_host_apis()
        self.cb_mic["values"] = get_input_devices(defaultHost)
        self.cb_speaker["values"] = get_output_devices(defaultHost)

        # Setting previous options
        if sj.cache["hostAPI"] not in self.cb_hostAPI["values"]:
            self.hostAPI_set_default(onInit=True)
        else:
            self.cb_hostAPI.set(sj.cache["hostAPI"])

        # if the previous mic is not available, set to default
        if sj.cache["mic"] not in self.cb_mic["values"]:
            self.mic_set_default()
        else:
            self.cb_mic.set(sj.cache["mic"])

        # If the previous speaker is not available, set to default
        if sj.cache["speaker"] not in self.cb_speaker["values"]:
            self.speaker_set_default()
        else:
            self.cb_speaker.set(sj.cache["speaker"])

    def input_device_menu(self, theType: Literal["hostAPI", "mic", "speaker"]):
        """
        Return a menu for input device combobox

        Args:
            theType (Literal["hostAPI", "mic", "speaker"]): The type of the combobox

        Returns:
            List[str]: A list of menu items
        """
        refreshDict = {
            "hostAPI": self.hostAPI_refresh,
            "mic": self.mic_refresh,
            "speaker": self.speaker_refresh,
        }

        setDefaultDict = {
            "hostAPI": self.hostAPI_set_default,
            "mic": self.mic_set_default,
            "speaker": self.speaker_set_default,
        }

        getDefaultDict = {
            "hostAPI": get_default_host_api,
            "mic": get_default_input_device,
            "speaker": get_default_output_device,
        }

        menu = tk.Menu(self.btn_config_hostAPI, tearoff=0)
        menu.add_command(label="Refresh", command=refreshDict[theType])
        menu.add_command(label="Set to default", command=setDefaultDict[theType])

        success, default_host = getDefaultDict[theType]()
        if success:
            assert isinstance(default_host, Dict)
            menu.add_separator()
            menu.add_command(label=f"Default: {default_host['name']}", state=tk.DISABLED)

        return menu

    def hostAPI_change(self, _event=None):
        """
        Change hostAPI combobox

        Will try to keep the previous mic and speaker if available.
        If not available, will try to get the default device (which may not match because of the difference in hostAPI).
        """
        self.cb_mic["values"] = get_input_devices(self.cb_hostAPI.get())
        self.cb_speaker["values"] = get_output_devices(self.cb_hostAPI.get())

        # Search mic
        prevName = self.cb_mic.get().split("|")[1].strip()
        found, index = False, 0
        for i, name in enumerate(self.cb_mic["values"]):
            if prevName in name:
                found, index = True, i
                break
        if found:
            self.cb_mic.current(index)
        else:
            self.mic_set_default()

        # Search speaker
        prevName = self.cb_speaker.get().split("|")[1].strip()
        found, index = False, 0
        for i, name in enumerate(self.cb_speaker["values"]):
            if prevName in name:
                found, index = True, i
                break
        if found:
            self.cb_speaker.current(index)
        else:
            self.speaker_set_default()

    def hostAPI_refresh(self, _event=None):
        """
        Refresh hostAPI list and check whether the current hostAPI is still available.
        """
        self.cb_hostAPI["values"] = get_host_apis()
        # verify if the current hostAPI is still available
        if self.cb_hostAPI.get() not in self.cb_hostAPI["values"]:
            self.cb_hostAPI.current(0)

        self.menu_hostAPI = self.input_device_menu("hostAPI")

    def hostAPI_set_default(self, _event=None, onInit=False):
        """
        Set hostAPI to default. Will update the list first.
        -> Show warning error if no default hostAPI found
        -> Set to default hostAPI if found, but will set to the first hostAPI if the default hostAPI is not available
        """
        self.hostAPI_refresh()  # update list
        success, default_host = get_default_host_api()
        if not success:
            if not ["supress_device_warning"]:
                self.errorNotif(str(default_host))

            self.cb_hostAPI.set("[ERROR] Getting default hostAPI failed")
        else:
            assert isinstance(default_host, Dict)
            if default_host["name"] not in self.cb_hostAPI["values"]:
                logger.warning(f"Default hostAPI {default_host['name']} not found, set to {self.cb_hostAPI['values'][0]}")
                if not ["supress_device_warning"]:
                    self.errorNotif(
                        f"Default hostAPI {default_host['name']} not found, set to {self.cb_hostAPI['values'][0]}"
                    )
                self.cb_hostAPI.current(0)
            else:
                self.cb_hostAPI.set(default_host["name"])
            sj.save_key("hostAPI", self.cb_hostAPI.get())

        # update the mic and speaker combobox
        if not onInit:
            self.hostAPI_change()

    # mic
    def mic_refresh(self, _event=None):
        """
        Refresh microphone list while also checking if the device is still available.
        """
        self.cb_mic["values"] = get_input_devices(self.cb_hostAPI.get())
        if self.cb_mic.get() not in self.cb_mic["values"]:
            self.cb_mic.current(0)

        self.menu_mic = self.input_device_menu("mic")

    def mic_set_default(self, _event=None):
        """
        Set microphone to default. Will update the list first.
        -> Show warning error if no default mic found
        -> Will search from the currently updated list and set it to the first mic if the default mic is not available
        """
        self.mic_refresh()  # update list
        success, default_device = get_default_input_device()
        if not success:
            if not ["supress_device_warning"]:
                self.errorNotif(str(default_device))

            self.cb_mic.set("[ERROR] No default mic found")
        else:
            assert isinstance(default_device, Dict)
            found = False
            index = 0
            for i, name in enumerate(self.cb_mic["values"]):
                if default_device["name"] in name:
                    found = True
                    index = i
                    break

            if not found:
                logger.warning(f"Default mic {default_device['name']} not found, set to {self.cb_mic['values'][0]}")
                if not ["supress_device_warning"]:
                    self.errorNotif(f"Default mic {default_device['name']} not found, set to {self.cb_mic['values'][0]}")
                self.cb_mic.current(0)
            else:
                self.cb_mic.set(self.cb_mic["values"][index])
            sj.save_key("mic", self.cb_mic.get())

    # speaker
    def speaker_refresh(self, _event=None):
        """
        Refresh speaker list while also checking if the device is still available.
        """
        self.cb_speaker["values"] = get_output_devices(self.cb_hostAPI.get())
        if self.cb_speaker.get() not in self.cb_speaker["values"]:
            self.cb_speaker.current(0)

        self.menu_speaker = self.input_device_menu("speaker")

    def speaker_set_default(self, _event=None):
        """
        Set speaker to default.  Will update the list first.
        -> If fail to get speaker, show warning error.
        """
        self.speaker_refresh()  # update list
        success, default_device = get_default_output_device()

        if not success:
            if not ["supress_device_warning"]:
                self.errorNotif(str(default_device))

            self.cb_speaker.set("[ERROR] No default speaker found")
        else:
            assert isinstance(default_device, Dict)
            found = False
            index = 0
            for i, name in enumerate(self.cb_speaker["values"]):
                if default_device["name"] in name:
                    found = True
                    index = i
                    break
            if not found:
                logger.warning(f"Default speaker {default_device['name']} not found, set to {self.cb_speaker['values'][0]}")
                if not ["supress_device_warning"]:
                    self.errorNotif(
                        f"Default speaker {default_device['name']} not found, set to {self.cb_speaker['values'][0]}"
                    )
                self.cb_speaker.current(0)
            else:
                self.cb_speaker.set(self.cb_speaker["values"][index])
            sj.save_key("speaker", self.cb_speaker.get())

    def cb_engine_change(self, _event=None):
        sj.save_key("tl_engine", self.cb_engine.get())
        self.cb_lang_update()

    def cb_lang_update(self):
        """
        update the target cb list with checks
        """
        # update the target cb list
        self.cb_targetLang["values"] = engine_select_target_dict[self.cb_engine.get()]

        # update source only if mode is not transcribe only
        if "selected" in self.cbtn_task_translate.state():
            self.cb_sourceLang["values"] = engine_select_source_dict[self.cb_engine.get()]

        # check if the target lang is not in the new list
        if self.cb_targetLang.get() not in self.cb_targetLang["values"]:
            self.cb_targetLang.current(0)

        # check if the source lang is not in the new list
        if self.cb_sourceLang.get() not in self.cb_sourceLang["values"]:
            self.cb_sourceLang.current(0)

        # save
        sj.save_key("sourceLang", self.cb_sourceLang.get())
        sj.save_key("targetLang", self.cb_targetLang.get())

    # clear textboxes
    def tb_clear(self):
        gc.clearMwTc()
        gc.clearMwTl()
        gc.clearExTc()
        gc.clearExTl()

    # Swap textboxes
    def tb_swap_content(self):
        tmp = self.tb_transcribed.get(1.0, "end")
        self.tb_transcribed.delete(1.0, "end")
        self.tb_transcribed.insert("end", self.tb_translated.get(1.0, "end"))
        self.tb_translated.delete(1.0, "end")
        self.tb_translated.insert("end", tmp)

    # swap select language and textbox
    def cb_swap_lang(self):
        # swap lang
        tmpTarget = self.cb_targetLang.get()
        tmpSource = self.cb_sourceLang.get()
        self.cb_sourceLang.set(tmpTarget)
        self.cb_targetLang.set(tmpSource)

        if self.cb_targetLang.get() == "Auto detect":
            self.cb_targetLang.current(0)

        # save
        sj.save_key("sourceLang", self.cb_sourceLang.get())
        sj.save_key("targetLang", self.cb_targetLang.get())

        # swap text only if mode is transcribe and translate
        if "selected" in self.cbtn_task_transcribe.state() and "selected" in self.cbtn_task_translate.state():
            self.tb_swap_content()

    # change mode
    def mode_change(self, _event=None):
        if "selected" in self.cbtn_task_transcribe.state() and "selected" in self.cbtn_task_translate.state():
            self.tb_translated_bg.pack_forget()
            self.tb_translated.pack_forget()

            self.tb_transcribed_bg.pack_forget()
            self.tb_transcribed.pack_forget()

            self.tb_transcribed_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_transcribed.pack(fill="both", expand=True, padx=1, pady=1)

            self.tb_translated_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_translated.pack(fill="both", expand=True, padx=1, pady=1)

            self.cb_sourceLang.configure(state="readonly")
            self.cb_targetLang.configure(state="readonly")
            self.cb_engine.configure(state="readonly")
            self.enable_processing()

        elif "selected" in self.cbtn_task_transcribe.state() and not "selected" in self.cbtn_task_translate.state():
            # transcribe only
            self.tb_transcribed_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_transcribed.pack(fill="both", expand=True, padx=1, pady=1)

            self.tb_translated_bg.pack_forget()
            self.tb_translated.pack_forget()

            self.cb_sourceLang.configure(state="readonly")
            self.cb_targetLang.configure(state="disabled")
            self.cb_engine.configure(state="disabled")
            self.enable_processing()

        elif "selected" in self.cbtn_task_translate.state() and not "selected" in self.cbtn_task_transcribe.state():
            # translate only
            self.tb_transcribed_bg.pack_forget()
            self.tb_transcribed.pack_forget()

            self.tb_translated_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_translated.pack(fill="both", expand=True, padx=1, pady=1)

            self.cb_sourceLang.configure(state="readonly")
            self.cb_targetLang.configure(state="readonly")
            self.cb_engine.configure(state="readonly")
            self.enable_processing()

        else:  # bot not selected
            self.cb_sourceLang.configure(state="readonly")
            self.cb_targetLang.configure(state="readonly")
            self.cb_engine.configure(state="readonly")
            self.disable_processing()

    def disable_processing(self):
        self.btn_record.configure(state="disabled")
        self.btn_import_file.configure(state="disabled")
        self.tb_transcribed.configure(state="disabled")
        self.tb_translated.configure(state="disabled")

    def enable_processing(self):
        self.btn_record.configure(state="normal")
        self.btn_import_file.configure(state="normal")
        self.tb_transcribed.configure(state="normal")
        self.tb_translated.configure(state="normal")

    def disable_interactions(self):
        self.cbtn_task_transcribe.configure(state="disabled")
        self.cbtn_task_translate.configure(state="disabled")
        self.cb_mic.configure(state="disabled")
        self.cb_speaker.configure(state="disabled")
        self.btn_swap.configure(state="disabled")
        self.btn_record.configure(state="disabled")
        self.btn_import_file.configure(state="disabled")
        self.cb_model.configure(state="disabled")
        self.cb_engine.configure(state="disabled")
        self.cb_sourceLang.configure(state="disabled")
        self.cb_targetLang.configure(state="disabled")

    def enable_interactions(self):
        self.cbtn_task_transcribe.configure(state="normal")
        self.cbtn_task_translate.configure(state="normal")
        self.cb_mic.configure(state="readonly")
        self.cb_speaker.configure(state="readonly")
        self.btn_swap.configure(state="normal")
        self.btn_record.configure(state="normal")
        self.btn_import_file.configure(state="normal")
        self.cb_model.configure(state="readonly")
        self.cb_engine.configure(state="readonly")
        self.cb_sourceLang.configure(state="readonly")
        if not "selected" in self.cbtn_task_translate.state():
            self.cb_targetLang.configure(state="disabled")
        else:
            self.cb_targetLang.configure(state="readonly")

    def start_loadBar(self):
        self.loadBar.configure(mode="indeterminate")
        self.loadBar.start()

    def stop_loadBar(self, rec_type: Literal["mic", "speaker", "file", None] = None):
        self.loadBar.stop()
        self.loadBar.configure(mode="determinate")

        # **change text only**, the function is already set before in the rec function
        if rec_type == "mic" or rec_type == "speaker":
            if not gc.recording:
                return
            self.btn_record.configure(text="Stop")
        elif rec_type == "file":
            self.btn_import_file.configure(text="Import", command=self.import_file)
            self.enable_interactions()

    def get_args(self):
        return (
            "selected" in self.cbtn_task_transcribe.state(),
            "selected" in self.cbtn_task_translate.state(),
            self.cb_model.get(),
            self.cb_engine.get(),
            self.cb_sourceLang.get().lower(),
            self.cb_targetLang.get().lower(),
            self.cb_mic.get(),
            self.cb_speaker.get(),
        )

    # ------------------ Export ------------------
    def export_tc(self):
        fileName = f"Transcribed {time.strftime('%Y-%m-%d %H-%M-%S')}"
        text = str(self.tb_transcribed.get(1.0, "end"))

        f = filedialog.asksaveasfile(
            mode="w", defaultextension=".txt", initialfile=fileName, filetypes=(("Text File", "*.txt"), ("All Files", "*.*"))
        )
        if f is None:
            return

        f.write("")
        f.close()

        # open file write it
        with open(f.name, "w", encoding="utf-8") as f:
            f.write(text)

        # open folder
        start_file(f.name)

    def export_tl(self):
        fileName = f"Translated {time.strftime('%Y-%m-%d %H-%M-%S')}"
        text = str(self.tb_translated.get(1.0, "end"))

        f = filedialog.asksaveasfile(
            mode="w", defaultextension=".txt", initialfile=fileName, filetypes=(("Text File", "*.txt"), ("All Files", "*.*"))
        )
        if f is None:
            return
        f.write("")
        f.close()

        # open file write it
        with open(f.name, "w", encoding="utf-8") as f:
            f.write(text)

        # open folder
        start_file(os.path.dirname(f.name))

    # TODO: maybe save the result to memory first so we can export like when using file import?
    def export_result(self):
        # check based on mode
        if "selected" in self.cbtn_task_transcribe.state() and not "selected" in self.cbtn_task_translate.state():
            text = str(self.tb_transcribed.get(1.0, "end"))

            if len(text.strip()) == 0:
                mbox("Could not export!", "No text to export", 1)
                return

            self.export_tc()
        elif not "selected" in self.cbtn_task_transcribe.state() and "selected" in self.cbtn_task_translate.state():
            text = str(self.tb_translated.get(1.0, "end"))

            if len(text.strip()) == 0:
                mbox("Could not export!", "No text to export", 1)
                return

            self.export_tl()
        elif "selected" in self.cbtn_task_transcribe.state() and "selected" in self.cbtn_task_translate.state():
            text = str(self.tb_transcribed.get(1.0, "end"))

            if len(text.strip()) == 0:
                mbox("Could not export!", "No text to export", 1)
                return

            self.export_tc()
            self.export_tl()

    def modelDownloadCancel(self):
        if not mbox("Cancel confirmation", "Are you sure you want to cancel downloading?", 3, self.root):
            return

        gc.cancel_dl = True  # Raise flag to stop

    def after_model_dl(self, taskname, task):
        # ask if user wants to continue using the model
        if mbox("Model is now Ready!", f"Continue task? ({taskname})", 3, self.root):
            task()

    def destroy_transient_toplevel(self, name, similar=False):
        for child in self.root.winfo_children():
            if isinstance(child, tk.Toplevel):
                if child.title() == name:
                    child.destroy()
                    break
                if similar and name in child.title():
                    child.destroy()
                    break

    # ------------------ Rec ------------------
    def rec(self):
        is_speaker = "selected" in self.radio_speaker.state()
        if is_speaker and platform.system() != "Windows":  # double checking. Speaker input is only available on Windows
            mbox(
                "Not available",
                """This feature is only available on Windows. 
                \rIn order to record PC sound from OS other than Windows you will need to create a virtual audio loopback to pass the speaker output as an input. You can use software like PulseAudio or Blackhole (on Mac) to do this.
                \rAfter that you can change your default input device to the virtual audio loopback.""",
                0,
                self.root,
            )
            return

        if gc.dl_thread and gc.dl_thread.is_alive():
            mbox(
                "Please wait! A model is being downloaded",
                "A Model is still being downloaded! Please wait until it finishes first!",
                1,
            )
            return

        # Checking args
        tc, tl, modelKey, engine, sourceLang, targetLang, mic, speaker = self.get_args()
        if sourceLang == targetLang and (tc and tl):
            mbox("Invalid options!", "Source and target language cannot be the same", 2)
            return

        # check model first
        modelName = append_dot_en(modelKey, sourceLang == "english")
        if not verify_model(modelName):
            if mbox(
                "Model is not downloaded yet!",
                f"`{modelName}` Model not found! You will need to download it first!\n\nDo you want to download it now?",
                3,
                self.root,
            ):
                logger.info("Downloading model...")
                try:
                    gc.dl_thread = threading.Thread(
                        target=download_model,
                        args=(
                            modelName,
                            self.root,
                            self.modelDownloadCancel,
                            lambda: self.after_model_dl("mic record", self.rec),
                        ),
                        daemon=True,
                    )
                    gc.dl_thread.start()
                except Exception as e:
                    logger.exception(e)
                    self.errorNotif(str(e))
            return

        # ui changes
        self.tb_clear()
        self.start_loadBar()
        self.disable_interactions()
        self.btn_record.configure(text="Loading", command=self.rec_stop, state="normal")

        gc.enableRecording()  # Flag update    # Disable recording is by button input

        # Start thread
        try:
            device = mic if not is_speaker else speaker
            recThread = threading.Thread(
                target=record_realtime,
                args=(sourceLang, targetLang, engine, modelKey, device, tc, tl, is_speaker),
                daemon=True,
            )
            recThread.start()
        except Exception as e:
            logger.exception(e)
            self.errorNotif(str(e))
            self.rec_stop()
            self.after_rec_stop()

    def rec_stop(self):
        logger.info("Recording Stopped")
        gc.disableRecording()

        self.btn_record.configure(text="Stopping...", state="disabled")

    def after_rec_stop(self):
        try:
            self.loadBar.stop()
            self.loadBar.configure(mode="determinate")
            self.btn_record.configure(text="Record", command=self.rec)
            self.enable_interactions()
        except Exception as e:
            logger.exception(e)

    # From file
    def import_file(self):
        if gc.dl_thread and gc.dl_thread.is_alive():
            mbox(
                "Please wait! A model is being downloaded",
                "A Model is still being downloaded! Please wait until it finishes first!",
                1,
            )
            return

        # Checking args
        tc, tl, modelKey, engine, sourceLang, targetLang, mic, speaker = self.get_args()
        if sourceLang == targetLang and (tc and tl):
            mbox("Invalid options!", "Source and target language cannot be the same", 2)
            return

        # check model first
        modelName = append_dot_en(modelKey, sourceLang == "english")
        if not verify_model(modelName):
            if mbox(
                "Model is not downloaded yet!",
                f"`{modelName}` Model not found! You will need to download it first!\n\nDo you want to download it now?",
                3,
                self.root,
            ):
                logger.info("Downloading model...")
                try:
                    gc.dl_thread = threading.Thread(
                        target=download_model,
                        args=(
                            modelName,
                            self.root,
                            self.modelDownloadCancel,
                            lambda: self.after_model_dl("file import", self.import_file),
                        ),
                        daemon=True,
                    )
                    gc.dl_thread.start()
                except Exception as e:
                    logger.exception(e)
                    self.errorNotif(str(e))
            return

        # get file
        files = filedialog.askopenfilenames(
            title="Select a file",
            filetypes=(
                ("Audio files", "*.wav *.mp3 *.ogg *.flac *.aac *.wma *.m4a"),
                ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
                ("All files", "*.*"),
            ),
        )

        if len(files) == 0:
            return

        # ui changes
        self.tb_clear()
        self.start_loadBar()
        self.disable_interactions()
        self.btn_import_file.configure(text="Loading", command=lambda: self.from_file_stop(True), state="normal")

        gc.enableRecording()  # Flag update

        # Start thread
        try:
            recFileThread = threading.Thread(
                target=file_input, args=(list(files), modelKey, sourceLang, targetLang, tc, tl, engine), daemon=True
            )
            recFileThread.start()
        except Exception as e:
            logger.exception(e)
            self.errorNotif(str(e))
            self.from_file_stop()

    def from_file_stop(self, prompt=False, notify=True):
        if prompt:
            if not mbox("Confirm", "Are you sure you want to cancel the file transcribe/translate process?", 3, self.root):
                return

        logger.info("Cancelling file import processing...")
        gc.disableRecording()
        gc.disableTranscribing()
        gc.disableTranslating()
        self.destroy_transient_toplevel("File Import Progress")

        if notify:
            mbox(
                "Cancelled",
                f"Cancelled file import processing\n\nTranscribed {gc.file_tced_counter} and translated {gc.file_tled_counter} file",
                0,
                self.root,
            )

        self.loadBar.stop()
        self.loadBar.configure(mode="determinate")
        self.btn_import_file.configure(text="Import file", command=self.import_file)
        self.enable_interactions()


def get_gpu_info():
    result = ""
    try:
        gpu_count = torch.cuda.device_count()
        if gpu_count == 0:
            result = "No GPU detected"
        elif gpu_count == 1:
            result = torch.cuda.get_device_name(0)
        else:
            result = f"{gpu_count} GPUs detected"
    except Exception as e:
        logger.exception(e)
        result = "Failed to detect GPU"
    finally:
        return result


def check_cuda_and_gpu():
    result = ""
    try:
        if not torch.cuda.is_available():
            result = "CUDA is not available! Using CPU instead"
        else:
            count = torch.cuda.device_count()
            gpus = [torch.cuda.get_device_name(i) for i in range(count)]
            result = f"Using {count} GPU(s): {', '.join(gpus)}"
    except Exception as e:
        logger.exception(e)
        result = "CUDA fail to check! Failed to detect GPU"
    finally:
        return result


def main():
    logger.info(f"App Version: {__version__}")
    logger.info(f"OS: {platform.system()} {platform.release()} {platform.version()} | CPU: {platform.processor()}")
    logger.info(f"GPU: {get_gpu_info()} | CUDA: {check_cuda_and_gpu()}")

    # --- GUI ---
    AppTray()  # Start tray app in the background
    main = MainWindow()
    TcsWindow(main.root)
    TlsWindow(main.root)
    SettingWindow(main.root)
    LogWindow(main.root)
    AboutWindow(main.root)
    main.root.mainloop()  # Start main app
