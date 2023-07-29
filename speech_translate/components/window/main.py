import os
import time
import platform
import threading
import tkinter as tk
import torch
from tkinter import ttk, filedialog
from typing import Literal

import sounddevice as sd

from PIL import Image, ImageDraw
from pystray import Icon as icon
from pystray import Menu as menu
from pystray import MenuItem as item

from speech_translate._version import __version__
from speech_translate._path import app_icon
from speech_translate._contants import APP_NAME
from speech_translate.globals import sj, gc
from speech_translate.custom_logging import logger

from speech_translate.components.window.about import AboutWindow
from speech_translate.components.window.log import LogWindow
from speech_translate.components.window.setting import SettingWindow
from speech_translate.components.window.transcribed import TcsWindow
from speech_translate.components.window.translated import TlsWindow
from speech_translate.components.custom.message import mbox
from speech_translate.components.custom.tooltip import CreateToolTip

from speech_translate.utils.model_download import verify_model, download_model
from speech_translate.utils.helper import tb_copy_only, nativeNotify
from speech_translate.utils.style import set_ui_style, init_theme, get_theme_list, get_current_theme
from speech_translate.utils.helper import upFirstCase, startFile
from speech_translate.utils.helper_whisper import append_dot_en, modelKeys, modelSelectDict
from speech_translate.utils.language import engine_select_source_dict, engine_select_target_dict, whisper_compatible
from speech_translate.utils.record import getInputDevices, getOutputDevices, getDefaultOutputDevice, getDefaultInputDevice, file_input, record_realtime

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
    logger.info("Console window hidden. If it is not hidden (only minimized), try changing your default windows terminal to windows cmd.")
    gc.cw = hWnd
except Exception as e:
    logger.debug("Ignore this error if not running on Windows OR if not run directly from terminal (e.g. run from IDE)")
    logger.exception(e)
    pass


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
            gc.theme_lists.remove("sv-dark")
            gc.theme_lists.remove("sv-light")

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
        # mode
        self.lbl_mode = ttk.Label(self.f1_toolbar, text="Mode:")
        self.lbl_mode.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        self.cb_mode = ttk.Combobox(self.f1_toolbar, values=["Transcribe", "Translate", "Transcribe & Translate"], state="readonly")
        self.cb_mode.pack(side="left", fill="x", padx=5, pady=5, expand=False)
        self.cb_mode.bind("<<ComboboxSelected>>", self.cb_mode_change)

        # model
        self.lbl_model = ttk.Label(self.f1_toolbar, text="Model:")
        self.lbl_model.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        self.cb_model = ttk.Combobox(self.f1_toolbar, values=modelKeys, state="readonly")
        self.cb_model.pack(side="left", fill="x", padx=5, pady=5, expand=False)
        CreateToolTip(
            self.cb_model,
            """Model size, larger models are more accurate but slower and require more VRAM/CPU power. 
            \rIf you have a low end GPU, use Tiny or Base. Don't use large unless you really need it or have super computer because it's very slow.
            \rModel specs: \n- Tiny: ~1 GB Vram\n- Base: ~1 GB Vram\n- Small: ~2 GB Vram\n- Medium: ~5 GB Vram\n- Large: ~10 GB Vram""".strip(),
            wrapLength=400,
        )
        self.cb_model.bind("<<ComboboxSelected>>", lambda _: sj.savePartialSetting("model", modelSelectDict[self.cb_model.get()]))

        # engine
        self.lbl_engine = ttk.Label(self.f1_toolbar, text="TL Engine:")
        self.lbl_engine.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        self.cb_engine = ttk.Combobox(self.f1_toolbar, values=["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"], state="readonly")
        self.cb_engine.pack(side="left", fill="x", padx=5, pady=5, expand=False)
        self.cb_engine.bind("<<ComboboxSelected>>", self.cb_engine_change)

        # from
        self.lbl_source = ttk.Label(self.f1_toolbar, text="From:")
        self.lbl_source.pack(side="left", padx=5, pady=5)

        self.cb_sourceLang = ttk.Combobox(self.f1_toolbar, values=engine_select_source_dict["Whisper"], state="readonly")  # initial value
        self.cb_sourceLang.pack(side="left", padx=5, pady=5)
        self.cb_sourceLang.bind("<<ComboboxSelected>>", lambda _: sj.savePartialSetting("sourceLang", self.cb_sourceLang.get()))

        # to
        self.lbl_to = ttk.Label(self.f1_toolbar, text="To:")
        self.lbl_to.pack(side="left", padx=5, pady=5)

        self.cb_targetLang = ttk.Combobox(self.f1_toolbar, values=[upFirstCase(x) for x in whisper_compatible], state="readonly")  # initial value
        self.cb_targetLang.pack(side="left", padx=5, pady=5)
        self.cb_targetLang.bind("<<ComboboxSelected>>", lambda _: sj.savePartialSetting("targetLang", self.cb_targetLang.get()))

        # swap
        self.btn_swap = ttk.Button(self.f1_toolbar, text="Swap", command=self.cb_swap_lang)
        self.btn_swap.pack(side="left", padx=5, pady=5)

        # clear
        self.btn_clear = ttk.Button(self.f1_toolbar, text="Clear", command=self.tb_clear)
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
        self.tb_transcribed.config(yscrollcommand=self.sb_transcribed.set)
        self.sb_transcribed.config(command=self.tb_transcribed.yview)

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
        self.tb_translated.config(yscrollcommand=self.sb_translated.set)
        self.sb_translated.config(command=self.tb_translated.yview)

        # -- f3_toolbar
        self.f3_frameLeft = ttk.Frame(self.f3_toolbar)
        self.f3_frameLeft.pack(side="left", fill="x", expand=True)

        self.f3_leftRow1 = ttk.Frame(self.f3_frameLeft)
        self.f3_leftRow1.pack(side="top", fill="x", expand=True)

        self.f3_leftRow2 = ttk.Frame(self.f3_frameLeft)
        self.f3_leftRow2.pack(side="top", fill="x", expand=True)

        self.f3_frameRight = ttk.Frame(self.f3_toolbar)
        self.f3_frameRight.pack(side="right", fill="x", expand=True)

        self.label_mic = ttk.Label(self.f3_leftRow1, text="Microphone:", font="TkDefaultFont 9 bold", width=10, cursor="hand2")
        self.label_mic.pack(side="left", padx=5, pady=0, ipady=0)
        self.label_mic.bind("<Button-1>", self.label_microphone_Lclick)
        self.label_mic.bind("<Button-3>", self.label_microphone_Rclick)
        CreateToolTip(
            self.label_mic,
            """Speaker to record microphone. Action available:
        \r[-] Left click to refresh\n[-] Right click to set to default device
        \r**NOTES**:\nFormat of the device is {device name, hostAPI}
        \rThere are many hostAPI for your device and it is recommended to follow the default value, other than that it might not work or crash the app.""",
            wrapLength=400,
        )

        self.cb_mic = ttk.Combobox(self.f3_leftRow1, values=[], state="readonly", width=70)
        self.cb_mic.bind("<<ComboboxSelected>>", lambda _: sj.savePartialSetting("mic", self.cb_mic.get()))
        self.cb_mic.pack(side="left", padx=5, pady=0, ipady=0)
        CreateToolTip(
            self.cb_mic,
            """**NOTES**:\nFormat of the device is {device name, hostAPI}
        \rThere are many hostAPI for your device and it is recommended to follow the default value, other than that it might not work or crash the app.
        \rTo set default value you can right click on the label in the left""",
            wrapLength=400,
        )

        self.label_speaker = ttk.Label(self.f3_leftRow2, text="Speaker:", font="TkDefaultFont 9 bold", width=10, cursor="hand2")
        self.label_speaker.pack(side="left", padx=5, pady=0, ipady=0)
        self.label_speaker.bind("<Button-1>", self.label_speaker_Lclick)
        self.label_speaker.bind("<Button-3>", self.label_speaker_Rclick)
        CreateToolTip(
            self.label_speaker,
            """Speaker to record system audio. Action available:
        \r[-] Left click to refresh\n[-] Right click to set to default device
        \r**NOTES**:\nFormat of the device is {device name, hostAPI [ID: x]}
        \rThere are many hostAPI for your device and it is recommended to follow the default value, other than that it might not work or crash the app.""",
            wrapLength=400,
        )

        self.cb_speaker = ttk.Combobox(self.f3_leftRow2, values=[], state="readonly", width=70)
        self.cb_speaker.bind("<<ComboboxSelected>>", lambda _: sj.savePartialSetting("speaker", self.cb_speaker.get()))
        self.cb_speaker.pack(side="left", padx=5, pady=0, ipady=0)
        CreateToolTip(
            self.cb_speaker,
            """**NOTES**:\nFormat of the device is {device name, hostAPI [ID: x]}
        \rThere are many hostAPI for your device and it is recommended to follow the default value, other than that it might not work or crash the app.
        \rTo set default value you can right click on the label in the left.""",
            wrapLength=400,
        )

        self.sep_btn_f3 = ttk.Separator(self.f3_leftRow1, orient="vertical")
        self.sep_btn_f3.pack(side="left", fill="y", pady=0, ipady=0)

        self.sep_btn_f3 = ttk.Separator(self.f3_leftRow2, orient="vertical")
        self.sep_btn_f3.pack(side="left", fill="y", pady=0, ipady=0)

        self.btn_record_mic = ttk.Button(self.f3_frameRight, text="Record From Mic", command=self.mic_rec)
        self.btn_record_mic.pack(side="right", padx=5, pady=5)
        CreateToolTip(self.btn_record_mic, "Record sound from selected microphone device")

        self.btn_record_speaker = ttk.Button(self.f3_frameRight, text="Record PC Sound", command=self.speaker_rec)
        self.btn_record_speaker.pack(side="right", padx=5, pady=5)
        CreateToolTip(self.btn_record_speaker, "Record sound from selected speaker device ")

        self.btn_import_file = ttk.Button(self.f3_frameRight, text="Import file (Audio/Video)", command=self.from_file)
        self.btn_import_file.pack(side="right", padx=5, pady=5)
        CreateToolTip(self.btn_import_file, "Transcribe/Translate from a file (video or audio)")

        # separator
        self.sep_btns_f3 = ttk.Separator(self.f3_frameRight, orient="vertical")
        self.sep_btns_f3.pack(side="right", fill="y", padx=5, pady=5)

        # export button
        self.btn_export = ttk.Button(self.f3_frameRight, text="Export Results", command=self.export_result)
        self.btn_export.pack(side="right", padx=5, pady=5)
        CreateToolTip(self.btn_export, "Export results to a file (txt)\nYou can also customize the export format\n\nFor srt export with timestamps please use import file.", wrapLength=250)

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
        self.fm_generate.add_command(label="Transcribed Speech Subtitle Window", command=self.open_detached_tcw, accelerator="F3")
        self.fm_generate.add_command(label="Translated Speech Subtitle Window", command=self.open_detached_tlw, accelerator="F4")
        self.menubar.add_cascade(label="Generate", menu=self.fm_generate)

        self.fm_help = tk.Menu(self.menubar, tearoff=0)
        self.fm_help.add_command(label="About", command=self.open_about, accelerator="F1")
        self.menubar.add_cascade(label="Help", menu=self.fm_help)

        self.root.config(menu=self.menubar)

        # ------------------ Bind keys ------------------
        self.root.bind("<F1>", self.open_about)
        self.root.bind("<F2>", self.open_setting)
        self.root.bind("<F3>", self.open_detached_tcw)
        self.root.bind("<F4>", self.open_detached_tlw)

        # ------------------ on Start ------------------
        # Start polling
        self.root.after(1000, self.isRunningPoll)
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
            sj.savePartialSetting("mw_size", f"{w}x{h}")

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

        logger.info("Exiting...")
        try:
            os._exit(0)
        except SystemExit:
            logger.info("Exit successful")

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
    def isRunningPoll(self):
        if not gc.running:
            self.quit_app()

        self.root.after(1000, self.isRunningPoll)

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

    # on start
    def onInit(self):
        self.cb_mode.set(sj.cache["mode"])
        self.cb_model.set({v: k for k, v in modelSelectDict.items()}[sj.cache["model"]])
        self.cb_sourceLang.set(sj.cache["sourceLang"])
        self.cb_targetLang.set(sj.cache["targetLang"])
        self.cb_engine.set(sj.cache["tl_engine"])

        # update on start
        self.cb_engine_change()
        self.cb_mode_change()
        self.cb_input_device_init()

    # mic
    def cb_input_device_init(self):
        """
        Initialize input device combobox

        Will check previous options and set to default if not available.
        If default is not available, will show a warning.
        """
        self.cb_mic["values"] = getInputDevices()
        self.cb_speaker["values"] = getOutputDevices()

        # if the previous mic is not available, set to default
        if sj.cache["mic"] not in self.cb_mic["values"]:
            self.label_microphone_Rclick()
        else:
            # verify if atleast one mic is available
            success, default_device = getDefaultInputDevice()
            if not success:
                if not ["supress_device_warning"]:
                    self.errorNotif(str(default_device))
                
                self.cb_mic.set("[ERROR] No default mic found")
                return

            self.cb_mic.set(sj.cache["mic"])

        # same
        if sj.cache["speaker"] not in self.cb_speaker["values"]:
            self.label_speaker_Rclick()
        else:
            success, default_device = getDefaultOutputDevice()
            if not success:
                if not ["supress_device_warning"]:
                    self.errorNotif(str(default_device))
                
                self.cb_mic.set("[ERROR] No default mic found")
                return

            self.cb_speaker.set(sj.cache["speaker"])

    def label_microphone_Lclick(self, _event=None):
        """
        Refresh microphone list
        """
        self.cb_mic["values"] = getInputDevices()
        # verify if the current mic is still available
        if self.cb_mic.get() not in self.cb_mic["values"]:
            self.cb_mic.current(0)

    def label_microphone_Rclick(self, _event=None):
        """
        Set microphone to default. Show warning error if no default mic found.
        """
        self.label_microphone_Lclick()  # update list
        success, default_device = getDefaultInputDevice()
        if not success:
            if not ["supress_device_warning"]:
                self.errorNotif(str(default_device))
            
            self.cb_mic.set("[ERROR] No default mic found")
            return

        if default_device:
            self.cb_mic.set(default_device["name"] + ", " + sd.query_hostapis(default_device["hostapi"])["name"])  # type: ignore
            sj.savePartialSetting("mic", self.cb_mic.get())
            # verify if the current mic is still available
            if self.cb_mic.get() not in self.cb_mic["values"]:
                self.cb_mic.current(0)
        else:
            self.errorNotif("No default mic found")

    # speaker
    def label_speaker_Lclick(self, _event=None):
        """
        Refresh speaker list
        """
        self.cb_speaker["values"] = getOutputDevices()
        # verify if the current speaker is still available
        if self.cb_speaker.get() not in self.cb_speaker["values"]:
            self.cb_speaker.current(0)

    def label_speaker_Rclick(self, _event=None):
        """
        Set speaker to default. Show warning error if no default speaker found.
        """
        self.label_speaker_Lclick()  # update list
        success, default_device = getDefaultOutputDevice()
        if not success:
            if not ["supress_device_warning"]:
                self.errorNotif(str(default_device))

            self.cb_speaker.set("[ERROR] No default speaker found")
            return

        if default_device:
            self.cb_speaker.set(f"{default_device['name']}, {sd.query_hostapis(default_device['hostApi'])['name']} [ID: {default_device['index']}]")  # type: ignore
            sj.savePartialSetting("speaker", self.cb_speaker.get())
            # verify if the current speaker is still available
            if self.cb_speaker.get() not in self.cb_speaker["values"]:
                self.cb_speaker.current(0)
        else:
            self.errorNotif("No default speaker found")

    def cb_engine_change(self, _event=None):
        sj.savePartialSetting("tl_engine", self.cb_engine.get())
        self.cb_lang_update()

    def cb_lang_update(self):
        """
        update the target cb list with checks
        """
        # update the target cb list
        self.cb_targetLang["values"] = engine_select_target_dict[self.cb_engine.get()]

        # update source only if mode is not transcribe only
        mode = self.cb_mode.get()
        if mode != "Transcribe":
            self.cb_sourceLang["values"] = engine_select_source_dict[self.cb_engine.get()]

        # check if the target lang is not in the new list
        if self.cb_targetLang.get() not in self.cb_targetLang["values"]:
            self.cb_targetLang.current(0)

        # check if the source lang is not in the new list
        if self.cb_sourceLang.get() not in self.cb_sourceLang["values"]:
            self.cb_sourceLang.current(0)

        # save
        sj.savePartialSetting("sourceLang", self.cb_sourceLang.get())
        sj.savePartialSetting("targetLang", self.cb_targetLang.get())

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

        # save
        sj.savePartialSetting("sourceLang", self.cb_sourceLang.get())
        sj.savePartialSetting("targetLang", self.cb_targetLang.get())

        # swap text only if mode is transcribe and translate
        if self.cb_mode.current() == 2:
            self.tb_swap_content()

    # change mode
    def cb_mode_change(self, _event=None):
        # get index of cb mode
        index = self.cb_mode.current()

        if index == 0:  # transcribe only
            self.tb_transcribed_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_transcribed.pack(fill="both", expand=True, padx=1, pady=1)

            self.tb_translated_bg.pack_forget()
            self.tb_translated.pack_forget()

            self.cb_sourceLang.config(state="readonly")
            self.cb_targetLang.config(state="disabled")

            # reset source lang selection
            self.cb_sourceLang["values"] = engine_select_source_dict["Whisper"]
        elif index == 1:  # translate only
            self.tb_transcribed_bg.pack_forget()
            self.tb_transcribed.pack_forget()

            self.tb_translated_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_translated.pack(fill="both", expand=True, padx=1, pady=1)

            self.cb_sourceLang.config(state="readonly")
            self.cb_targetLang.config(state="readonly")
            self.cb_lang_update()

        elif index == 2:  # transcribe and translate
            self.tb_translated_bg.pack_forget()
            self.tb_translated.pack_forget()

            self.tb_transcribed_bg.pack_forget()
            self.tb_transcribed.pack_forget()

            self.tb_transcribed_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_transcribed.pack(fill="both", expand=True, padx=1, pady=1)

            self.tb_translated_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_translated.pack(fill="both", expand=True, padx=1, pady=1)

            self.cb_sourceLang.config(state="readonly")
            self.cb_targetLang.config(state="readonly")
            self.cb_lang_update()

        # save
        sj.savePartialSetting("mode", self.cb_mode.get())

    def disable_interactions(self):
        self.cb_mode.config(state="disabled")
        self.cb_model.config(state="disabled")
        self.cb_engine.config(state="disabled")
        self.cb_sourceLang.config(state="disabled")
        self.cb_targetLang.config(state="disabled")
        self.cb_mic.config(state="disabled")
        self.cb_speaker.config(state="disabled")
        self.btn_swap.config(state="disabled")
        self.btn_record_mic.config(state="disabled")
        self.btn_record_speaker.config(state="disabled")
        self.btn_import_file.config(state="disabled")

    def enable_interactions(self):
        self.cb_mode.config(state="readonly")
        self.cb_model.config(state="readonly")
        self.cb_engine.config(state="readonly")
        self.cb_sourceLang.config(state="readonly")
        if self.cb_mode.current() == 0:
            self.cb_targetLang.config(state="disabled")
        else:
            self.cb_targetLang.config(state="readonly")
        self.cb_mic.config(state="readonly")
        self.cb_speaker.config(state="readonly")
        self.btn_swap.config(state="normal")
        self.btn_record_mic.config(state="normal")
        self.btn_record_speaker.config(state="normal")
        self.btn_import_file.config(state="normal")

    def start_loadBar(self):
        self.loadBar.config(mode="indeterminate")
        self.loadBar.start()

    def stop_loadBar(self, rec_type: Literal["mic", "pc", "file", None] = None):
        self.loadBar.stop()
        self.loadBar.config(mode="determinate")

        # **change text only**, the function is already set before in the rec function
        if rec_type == "mic":
            if not gc.recording:
                return
            self.btn_record_mic.config(text="Stop")
        elif rec_type == "pc":
            if not gc.recording:
                return
            self.btn_record_speaker.config(text="Stop")
        elif rec_type == "file":
            self.btn_import_file.config(text="Import From File (Video/Audio)", command=self.from_file)
            self.enable_interactions()

    def get_args(self):
        return self.cb_mode.current(), self.cb_model.get(), self.cb_engine.get(), self.cb_sourceLang.get().lower(), self.cb_targetLang.get().lower(), self.cb_mic.get(), self.cb_speaker.get()

    # ------------------ Export ------------------
    def export_tc(self):
        fileName = f"Transcribed {time.strftime('%Y-%m-%d %H-%M-%S')}"
        text = str(self.tb_transcribed.get(1.0, "end"))

        f = filedialog.asksaveasfile(mode="w", defaultextension=".txt", initialfile=fileName, filetypes=(("Text File", "*.txt"), ("All Files", "*.*")))
        if f is None:
            return

        f.write("")
        f.close()

        # open file write it
        with open(f.name, "w", encoding="utf-8") as f:
            f.write(text)

        # open folder
        startFile(f.name)

    def export_tl(self):
        fileName = f"Translated {time.strftime('%Y-%m-%d %H-%M-%S')}"
        text = str(self.tb_translated.get(1.0, "end"))

        f = filedialog.asksaveasfile(mode="w", defaultextension=".txt", initialfile=fileName, filetypes=(("Text File", "*.txt"), ("All Files", "*.*")))
        if f is None:
            return
        f.write("")
        f.close()

        # open file write it
        with open(f.name, "w", encoding="utf-8") as f:
            f.write(text)

        # open folder
        startFile(os.path.dirname(f.name))

    def export_result(self):
        # check based on mode
        if self.cb_mode.current() == 0:  # transcribe only
            text = str(self.tb_transcribed.get(1.0, "end"))

            if len(text.strip()) == 0:
                mbox("Could not export!", "No text to export", 1)
                return

            self.export_tc()
        elif self.cb_mode.current() == 1:  # translate only
            text = str(self.tb_translated.get(1.0, "end"))

            if len(text.strip()) == 0:
                mbox("Could not export!", "No text to export", 1)
                return

            self.export_tl()
        elif self.cb_mode.current() == 2:  # transcribe and translate
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
    # From mic
    def mic_rec(self):
        if gc.dl_thread and gc.dl_thread.is_alive():
            mbox("Please wait! A model is being downloaded", "A Model is still being downloaded! Please wait until it finishes first!", 1)
            return

        # Checking args
        mode, modelKey, engine, sourceLang, targetLang, mic, speaker = self.get_args()
        if sourceLang == targetLang and mode == 2:
            mbox("Invalid options!", "Source and target language cannot be the same", 2)
            return

        # check model first
        modelName = append_dot_en(modelKey, sourceLang == "english")
        if not verify_model(modelName):
            if mbox("Model is not downloaded yet!", f"`{modelName}` Model not found! You will need to download it first!\n\nDo you want to download it now?", 3, self.root):
                logger.info("Downloading model...")
                try:
                    gc.dl_thread = threading.Thread(target=download_model, args=(modelName, self.root, self.modelDownloadCancel, lambda: self.after_model_dl("mic record", self.mic_rec)), daemon=True)
                    gc.dl_thread.start()
                except Exception as e:
                    logger.exception(e)
                    self.errorNotif(str(e))
            return

        # ui changes
        self.tb_clear()
        self.start_loadBar()
        self.disable_interactions()
        self.btn_record_mic.config(text="Loading", command=self.mic_rec_stop, state="normal")

        gc.enableRecording()  # Flag update    # Disable recording is by button input
        transcribe = mode == 0 or mode == 2
        translate = mode == 1 or mode == 2

        # Start thread
        try:
            recMicThread = threading.Thread(target=record_realtime, args=(sourceLang, targetLang, engine, modelKey, mic, transcribe, translate), daemon=True)
            recMicThread.start()
        except Exception as e:
            logger.exception(e)
            self.errorNotif(str(e))
            self.mic_rec_stop()
            self.after_mic_rec_stop()

    def mic_rec_stop(self):
        logger.info("Recording Mic Stopped")
        gc.disableRecording()

        self.btn_record_mic.config(text="Stopping...", state="disabled")

    def after_mic_rec_stop(self):
        try:
            self.loadBar.stop()
            self.loadBar.config(mode="determinate")
            self.btn_record_mic.config(text="Record From Mic", command=self.mic_rec)
            self.enable_interactions()
        except Exception as e:
            logger.exception(e)

    # From pc
    def speaker_rec(self):
        # check if on windows or not
        if platform.system() != "Windows":
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
            mbox("Please wait! A model is being downloaded", "A Model is still being downloaded! Please wait until it finishes first!", 1)
            return

        # Checking args
        mode, modelKey, engine, sourceLang, targetLang, mic, speaker = self.get_args()
        if sourceLang == targetLang and mode == 2:
            mbox("Invalid options!", "Source and target language cannot be the same", 2)
            return

        # check model first
        modelName = append_dot_en(modelKey, sourceLang == "english")
        if not verify_model(modelName):
            if mbox("Model is not downloaded yet!", f"`{modelName}` Model not found! You will need to download it first!\n\nDo you want to download it now?", 3, self.root):
                logger.info("Downloading model...")
                try:
                    gc.dl_thread = threading.Thread(target=download_model, args=(modelName, self.root, self.modelDownloadCancel, lambda: self.after_model_dl("speaker record", self.speaker_rec)), daemon=True)
                    gc.dl_thread.start()
                except Exception as e:
                    logger.exception(e)
                    self.errorNotif(str(e))
            return

        # ui changes
        self.tb_clear()
        self.start_loadBar()
        self.disable_interactions()
        self.btn_record_speaker.config(text="Loading", command=self.speaker_rec_stop, state="normal")

        gc.enableRecording()  # Flag update
        transcribe = mode == 0 or mode == 2
        translate = mode == 1 or mode == 2

        # Start thread
        try:
            recPcThread = threading.Thread(target=record_realtime, args=(sourceLang, targetLang, engine, modelKey, speaker, transcribe, translate, True), daemon=True)
            recPcThread.start()
        except Exception as e:
            logger.exception(e)
            self.errorNotif(str(e))
            self.speaker_rec_stop()
            self.after_speaker_rec_stop()

    def speaker_rec_stop(self):
        logger.info("Recording PC Stopped")
        gc.disableRecording()

        self.btn_record_speaker.config(text="Stopping...", state="disabled")

    def after_speaker_rec_stop(self):
        try:
            self.loadBar.stop()
            self.loadBar.config(mode="determinate")
            self.btn_record_speaker.config(text="Record PC Sound", command=self.speaker_rec)
            self.enable_interactions()
        except Exception as e:
            logger.exception(e)

    # From file
    def from_file(self):
        if gc.dl_thread and gc.dl_thread.is_alive():
            mbox("Please wait! A model is being downloaded", "A Model is still being downloaded! Please wait until it finishes first!", 1)
            return

        # Checking args
        mode, modelKey, engine, sourceLang, targetLang, mic, speaker = self.get_args()
        if sourceLang == targetLang and mode == 2:
            mbox("Invalid options!", "Source and target language cannot be the same", 2)
            return

        # check model first
        modelName = append_dot_en(modelKey, sourceLang == "english")
        if not verify_model(modelName):
            if mbox("Model is not downloaded yet!", f"`{modelName}` Model not found! You will need to download it first!\n\nDo you want to download it now?", 3, self.root):
                logger.info("Downloading model...")
                try:
                    gc.dl_thread = threading.Thread(target=download_model, args=(modelName, self.root, self.modelDownloadCancel, lambda: self.after_model_dl("file import", self.from_file)), daemon=True)
                    gc.dl_thread.start()
                except Exception as e:
                    logger.exception(e)
                    self.errorNotif(str(e))
            return

        # get file
        files = filedialog.askopenfilenames(
            title="Select a file",
            filetypes=(("Audio files", "*.wav *.mp3 *.ogg *.flac *.aac *.wma *.m4a"), ("Video files", "*.mp4 *.mkv *.avi *.mov"), ("All files", "*.*")),
        )

        if len(files) == 0:
            return

        # ui changes
        self.tb_clear()
        self.start_loadBar()
        self.disable_interactions()
        self.btn_import_file.config(text="Loading", command=lambda: self.from_file_stop(True), state="normal")

        gc.enableRecording()  # Flag update
        transcribe = mode == 0 or mode == 2
        translate = mode == 1 or mode == 2

        # Start thread
        try:
            recFileThread = threading.Thread(target=file_input, args=(list(files), modelKey, sourceLang, targetLang, transcribe, translate, engine), daemon=True)
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
            mbox("Cancelled", f"Cancelled file import processing\n\nTranscribed {gc.file_tced_counter} and translated {gc.file_tled_counter} file", 0, self.root)

        self.loadBar.stop()
        self.loadBar.config(mode="determinate")
        self.btn_import_file.config(text="Import From File (Video/Audio)", command=self.from_file)
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
        result = "Failed to detect GPU"
    finally:
        return result
