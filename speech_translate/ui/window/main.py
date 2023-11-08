import os
from platform import processor, release, system, version
from signal import SIGINT, signal  # Import the signal module to handle Ctrl+C
from threading import Thread
from time import strftime
from tkinter import Frame, Menu, StringVar, Tk, Toplevel, filedialog, ttk, Canvas
from typing import Dict, Literal

from loguru import logger
from PIL import Image, ImageDraw, ImageTk
from pystray import Icon as icon
from pystray import Menu as menu
from pystray import MenuItem as item
from torch import cuda
from stable_whisper import WhisperResult

from speech_translate._constants import APP_NAME
from speech_translate._path import app_icon, splash_image
from speech_translate._version import __version__
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.combobox import CategorizedComboBox, ComboboxWithKeyNav
from speech_translate.ui.custom.dialog import FileImportDialog, RefinementDialog, AlignmentDialog, TranslateResultDialog, prompt_with_choices
from speech_translate.ui.custom.message import mbox
from speech_translate.ui.custom.text import ColoredText
from speech_translate.ui.custom.tooltip import tk_tooltip, tk_tooltips
from speech_translate.ui.window.about import AboutWindow
from speech_translate.ui.window.log import LogWindow
from speech_translate.ui.window.setting import SettingWindow
from speech_translate.ui.window.transcribed import TcsWindow
from speech_translate.ui.window.translated import TlsWindow
from speech_translate._logging import init_logging
from speech_translate.globals import gc, sj
from speech_translate.utils.audio.device import (
    get_default_host_api, get_default_input_device, get_default_output_device, get_host_apis, get_input_devices,
    get_output_devices
)
from speech_translate.utils.helper import (
    OpenUrl, bind_focus_recursively, emoji_img, native_notify, open_folder, popup_menu, similar, tb_copy_only, up_first_case,
    windows_os_only, check_ffmpeg_in_path, install_ffmpeg
)
from speech_translate.utils.translate.language import (
    engine_select_source_dict, engine_select_target_dict, whisper_compatible
)
from speech_translate.utils.whisper.helper import append_dot_en, model_keys, model_select_dict, save_output_stable_ts
from speech_translate.utils.whisper.download import download_model, get_default_download_root, verify_model_faster_whisper, verify_model_whisper
from speech_translate.utils.audio.record import record_session
from speech_translate.utils.audio.file import process_file, mod_result, translate_result
from speech_translate.utils.tk.style import get_current_theme, get_theme_list, init_theme, set_ui_style


# Function to handle Ctrl+C and exit just like clicking the exit button
def signal_handler(sig, frame):
    logger.info("Received Ctrl+C, exiting...")
    gc.running = False


signal(SIGINT, signal_handler)  # Register the signal handler for Ctrl+C


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


class Splash(Toplevel):
    def __init__(self, parent, geometry):
        Toplevel.__init__(self, parent)
        self.title("Splash")
        self.geometry(geometry)
        self.overrideredirect(True)
        self.resizable(False, False)
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)

        self.x = 0
        self.y = 0
        self.bind("<Button-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.on_motion)

        # load image file
        try:
            self.image = Image.open(splash_image)
            self.image = self.image.resize((640, 360))
        except Exception:
            logger.error("Splash image not found")
            self.image = Image.new("RGB", (640, 360), "black")

        # load image to canvas
        self.canvas = Canvas(self, width=768, height=345, highlightthickness=0)
        self.canvas.pack(pady=0, ipady=0)

        self.imgtk = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 170, anchor="w", image=self.imgtk)

        self.loadbar = ttk.Progressbar(self, orient="horizontal", length=200, mode="indeterminate")
        self.loadbar.pack(side="bottom", fill="x", pady=0, ipady=0)
        self.loadbar.start(15)

        ## required to make window show before the program gets to the mainloop
        self.update()

    def start_move(self, event):
        self.x = event.x_root - self.winfo_x()
        self.y = event.y_root - self.winfo_y()

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_motion(self, event):
        if self.x is not None and self.y is not None:
            new_x = event.x_root - self.x
            new_y = event.y_root - self.y
            self.geometry("+%s+%s" % (new_x, new_y))


class MainWindow:
    """
    Main window of the app
    """
    def __init__(self):
        # ------------------ Window ------------------
        # UI
        gc.mw = self
        self.root = Tk()
        self.root.title(APP_NAME)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.minsize(600, 300)
        self.root.wm_attributes("-topmost", False)  # Default False

        # Flags
        self.always_on_top: bool = False
        self.notified_hidden: bool = False
        self.prompting = False

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

        self.splash = Splash(self.root, f"640x360+{self.root.winfo_x() + 300}+{self.root.winfo_y() + 200}")
        self.root.withdraw()

        gc.wrench_emoji = emoji_img(16, "     🛠️")
        gc.folder_emoji = emoji_img(13, " 📂")
        gc.open_emoji = emoji_img(13, "     ↗️")
        gc.trash_emoji = emoji_img(13, "     🗑️")
        gc.reset_emoji = emoji_img(13, " 🔄")
        gc.question_emoji = emoji_img(16, "❓")
        gc.cuda = check_cuda_and_gpu()

        # ------------------ Frames ------------------
        self.f1_toolbar = ttk.Frame(self.root)
        self.f1_toolbar.pack(side="top", fill="x", expand=False, pady=(5, 0))

        self.f2_textBox = ttk.Frame(self.root)
        self.f2_textBox.pack(side="top", fill="both", expand=True)

        self.f3_toolbar = ttk.Frame(self.root)
        self.f3_toolbar.pack(side="top", fill="x", expand=False)

        self.f4_statusbar = ttk.Frame(self.root)
        self.f4_statusbar.pack(side="bottom", fill="x", expand=False)

        # ------------------ Elements ------------------
        # -- f1_toolbar
        # model
        self.lbl_model = ttk.Label(self.f1_toolbar, text="Transcribe:")
        self.lbl_model.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        self.cb_model = ComboboxWithKeyNav(self.f1_toolbar, values=model_keys, state="readonly")
        self.cb_model.set({v: k for k, v in model_select_dict.items()}[sj.cache["model"]])
        self.cb_model.pack(side="left", fill="x", padx=5, pady=5, expand=True)
        self.cb_model.bind("<<ComboboxSelected>>", lambda _: sj.save_key("model", model_select_dict[self.cb_model.get()]))
        tk_tooltips(
            [self.lbl_model, self.cb_model],
            "Each Whisper model have different requirements. Please refer to the specs below:"
            "\n- Tiny: ~1 GB Vram\n- Base: ~1 GB Vram\n- Small: ~2 GB Vram\n- Medium: ~5 GB Vram\n- Large: ~10 GB Vram"
            "\n\nBy default, Speech Translate uses Faster-Whisper through Stable-Ts which according to its claim should "
            "make the model run 4 times faster for the same accuracy while using less memory (you can change this option in setting)",
            wrapLength=400,
        )

        # engine
        self.lbl_engine = ttk.Label(self.f1_toolbar, text="Translate:")
        self.lbl_engine.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        self.cb_engine = CategorizedComboBox(
            self.root, self.f1_toolbar, {
                "Whisper": model_keys,
                "Google Translate": [],
                "LibreTranslate": [],
                "MyMemoryTranslator": []
            }, self.cb_engine_change
        )
        self.cb_engine.set(sj.cache["tl_engine"])
        self.cb_engine.pack(side="left", fill="x", padx=5, pady=5, expand=True)
        tk_tooltips(
            [self.lbl_engine],
            "Same as transcribe, larger models are more accurate but are slower and require more power.\n"
            "It is recommended to use google translate for the best result. If you want full offline capability, "
            "you can use libretranslate by hosting it yourself locally",
            wrapLength=400,
        )

        # from
        self.lbl_source = ttk.Label(self.f1_toolbar, text="From:")
        self.lbl_source.pack(side="left", padx=5, pady=5)

        self.cb_source_lang = ComboboxWithKeyNav(
            self.f1_toolbar, values=engine_select_source_dict["Google Translate"], state="readonly"
        )  # initial value
        self.cb_source_lang.set(sj.cache["sourceLang"])
        self.cb_source_lang.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.cb_source_lang.bind("<<ComboboxSelected>>", lambda _: sj.save_key("sourceLang", self.cb_source_lang.get()))

        # to
        self.lbl_to = ttk.Label(self.f1_toolbar, text="To:")
        self.lbl_to.pack(side="left", padx=5, pady=5)

        self.cb_target_lang = ComboboxWithKeyNav(
            self.f1_toolbar, values=[up_first_case(x) for x in whisper_compatible], state="readonly"
        )  # initial value
        self.cb_target_lang.set(sj.cache["targetLang"])
        self.cb_target_lang.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.cb_target_lang.bind("<<ComboboxSelected>>", lambda _: sj.save_key("targetLang", self.cb_target_lang.get()))

        # swap
        self.btn_swap = ttk.Button(self.f1_toolbar, text="Swap", command=self.cb_swap_lang)
        self.btn_swap.pack(side="left", padx=5, pady=5)

        # clear
        self.btn_clear = ttk.Button(self.f1_toolbar, text="Clear", command=self.tb_clear, style="Accent.TButton")
        self.btn_clear.pack(side="left", padx=5, pady=5)

        # -- f2_textBox
        self.tb_transcribed_bg = Frame(self.f2_textBox, bg="#7E7E7E")
        self.tb_transcribed_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.sb_transcribed = ttk.Scrollbar(self.tb_transcribed_bg)
        self.sb_transcribed.pack(side="right", fill="y")

        self.tb_transcribed = ColoredText(
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

        self.tb_translated_bg = Frame(self.f2_textBox, bg="#7E7E7E")
        self.tb_translated_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.sb_translated = ttk.Scrollbar(self.tb_translated_bg)
        self.sb_translated.pack(side="right", fill="y")

        self.tb_translated = ColoredText(
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

        self.f3_1_row1 = ttk.Frame(self.f3_1)
        self.f3_1_row1.pack(side="top", fill="x")

        self.f3_1_row2 = ttk.Frame(self.f3_1)
        self.f3_1_row2.pack(side="top", fill="x")

        self.f3_1_row3 = ttk.Frame(self.f3_1)
        self.f3_1_row3.pack(side="top", fill="x")

        # -- hostAPI
        self.lbl_hostAPI = ttk.Label(self.f3_1_row1, text="HostAPI:", font="TkDefaultFont 9 bold", width=10)
        self.lbl_hostAPI.pack(side="left", padx=5, pady=0, ipady=0)
        tk_tooltip(
            self.lbl_hostAPI,
            "HostAPI for the input device. There are many hostAPI for your device and it is recommended to follow the "
            "default value, other than that it might not work or crash the app.",
            wrapLength=350,
        )

        self.cb_hostAPI = ComboboxWithKeyNav(self.f3_1_row1, values=[], state="readonly")
        self.cb_hostAPI.bind(
            "<<ComboboxSelected>>", lambda _: sj.save_key("hostAPI", self.cb_hostAPI.get()) or self.hostAPI_change()
        )
        self.cb_hostAPI.pack(side="left", padx=5, pady=0, ipady=0, expand=True, fill="x")

        self.btn_config_hostAPI = ttk.Button(
            self.f3_1_row1,
            image=gc.wrench_emoji,
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

        self.cb_mic = ComboboxWithKeyNav(self.f3_1_row2, values=[], state="readonly")
        self.cb_mic.bind("<<ComboboxSelected>>", lambda _: sj.save_key("mic", self.cb_mic.get()))
        self.cb_mic.pack(side="left", padx=5, pady=0, ipady=0, expand=True, fill="x")

        self.btn_config_mic = ttk.Button(
            self.f3_1_row2,
            image=gc.wrench_emoji,
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

        self.cb_speaker = ComboboxWithKeyNav(self.f3_1_row3, values=[], state="readonly")
        self.cb_speaker.bind("<<ComboboxSelected>>", lambda _: sj.save_key("speaker", self.cb_speaker.get()))
        self.cb_speaker.pack(side="left", padx=5, pady=0, ipady=0, expand=True, fill="x")

        self.btn_config_speaker = ttk.Button(
            self.f3_1_row3,
            image=gc.wrench_emoji,
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

        self.cbtn_task_transcribe = CustomCheckButton(
            self.f3_2_row2,
            sj.cache["transcribe"],
            lambda x: sj.save_key("transcribe", x) or self.mode_change(),
            text="Transcribe"
        )
        self.cbtn_task_transcribe.pack(side="left", padx=5, pady=2.5, ipady=0)

        self.cbtn_task_translate = CustomCheckButton(
            self.f3_2_row3,
            sj.cache["translate"],
            lambda x: sj.save_key("translate", x) or self.mode_change(),
            text="Translate"
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

        self.strvar_input = StringVar()
        self.radio_mic = ttk.Radiobutton(
            self.f3_3_row2,
            text="Microphone",
            value="mic",
            width=12,
            command=lambda: sj.save_key("input", "mic"),
            variable=self.strvar_input,
        )
        self.radio_mic.pack(side="left", padx=5, pady=2.5, ipady=0)

        self.radio_speaker = ttk.Radiobutton(
            self.f3_3_row3,
            text="Speaker",
            value="speaker",
            width=12,
            command=lambda: sj.save_key("input", "speaker"),
            variable=self.strvar_input,
        )
        self.radio_speaker.pack(side="left", padx=5, pady=2.5, ipady=0)
        self.strvar_input.set("mic" if sj.cache["input"] == "mic" else "speaker")

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

        # button
        self.btn_copy = ttk.Button(self.f3_4_row1, text="Copy", command=lambda: popup_menu(self.root, self.menu_copy))
        self.btn_copy.pack(side="right", padx=5, pady=5)
        tk_tooltip(self.btn_copy, "Copy the text to clipboard", wrapLength=250)

        self.menu_copy = Menu(self.root, tearoff=0)
        self.menu_copy.add_command(label="Copy transcribed text", command=lambda: self.copy_tb("transcribed"))
        self.menu_copy.add_command(label="Copy translated text", command=lambda: self.copy_tb("translated"))

        self.btn_tool = ttk.Button(self.f3_4_row2, text="Tool", command=lambda: popup_menu(self.root, self.menu_tool))
        self.btn_tool.pack(side="right", padx=5, pady=5)
        tk_tooltip(
            self.btn_tool,
            "Collection of tools to help you with adjusting the result.",
            wrapLength=250,
        )

        self.menu_tool = Menu(self.root, tearoff=0)
        self.menu_tool.add_command(label="Export Recorded Results", command=lambda: self.export_result())
        self.menu_tool.add_command(label="Align Results", command=lambda: self.align_file())
        self.menu_tool.add_command(label="Refine Results", command=lambda: self.refine_file())
        self.menu_tool.add_command(
            label="Translate Results (Whisper Result in .json)", command=lambda: self.translate_file()
        )

        # -- f4_statusbar
        # load bar
        self.loadBar = ttk.Progressbar(self.f4_statusbar, orient="horizontal", length=100, mode="determinate")
        self.loadBar.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # ------------------ Menubar ------------------
        self.menubar = Menu(self.root)
        self.fm_file = Menu(self.menubar, tearoff=0)
        self.fm_file.add_checkbutton(label="Stay on top", command=self.toggle_always_on_top)
        self.fm_file.add_separator()
        self.fm_file.add_command(label="Hide", command=lambda: self.root.withdraw())
        self.fm_file.add_command(label="Exit", command=self.quit_app)
        self.menubar.add_cascade(label="File", menu=self.fm_file)

        self.fm_view = Menu(self.menubar, tearoff=0)
        self.fm_view.add_command(label="Settings", command=self.open_setting, accelerator="F2")
        self.fm_view.add_command(label="Log", command=self.open_log, accelerator="Ctrl+F1")
        self.menubar.add_cascade(label="View", menu=self.fm_view)

        self.fm_show = Menu(self.menubar, tearoff=0)
        self.fm_show.add_command(
            label="Transcribed Speech Subtitle Window", command=self.open_detached_tcw, accelerator="F3"
        )
        self.fm_show.add_command(label="Translated Speech Subtitle Window", command=self.open_detached_tlw, accelerator="F4")
        self.menubar.add_cascade(label="Show", menu=self.fm_show)

        self.fm_help = Menu(self.menubar, tearoff=0)
        self.fm_help.add_command(label="About", command=self.open_about, accelerator="F1")
        self.fm_help.add_command(
            label="Open documentation / wiki",
            command=lambda: OpenUrl("https://github.com/Dadangdut33/Speech-Translate/wiki")
        )
        self.menubar.add_cascade(label="Help", menu=self.fm_help)

        self.root.configure(menu=self.menubar)

        # ------------------ Bind keys ------------------
        self.root.bind("<Control-F1>", self.open_log)
        self.root.bind("<F1>", self.open_about)
        self.root.bind("<F2>", self.open_setting)
        self.root.bind("<F3>", self.open_detached_tcw)
        self.root.bind("<F4>", self.open_detached_tlw)

        # ------------------ on Start ------------------
        bind_focus_recursively(self.root, self.root)
        self.splash.destroy()
        self.root.deiconify()
        self.root.geometry(sj.cache["mw_size"])
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        self.on_init()
        gc.running_after_id = self.root.after(1000, self.is_running_poll)
        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except Exception:
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

        gc.disable_rec()
        gc.disable_tc()
        gc.disable_tl()

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

        self.cleanup()
        logger.info("Exiting...")
        try:
            os._exit(0)
        except SystemExit:
            logger.info("Exit successful")

    def restart_app(self):
        if gc.transcribing or gc.translating or gc.recording or gc.file_processing or (
            gc.dl_thread and gc.dl_thread.is_alive()
        ):
            # prompt
            if not mbox(
                "Restarting app...",
                "There is a process still running, are you sure you want to restart the app?"
                "\n\nThis will stop the process "
                "and may cause data loss!",
                3,
            ):
                return

        # save window size
        self.save_win_size()
        gc.sw.save_win_size()  # type: ignore

        self.cleanup()
        logger.info("Restarting...")  # restart
        main(with_log_init=False)

    # Show window
    def show_window(self):
        self.root.after(0, self.root.deiconify)

    # Close window
    def on_close(self):
        self.save_win_size()

        # Only show notification once
        if not self.notified_hidden and not sj.cache["supress_hidden_to_tray"]:
            native_notify("Hidden to tray", "The app is still running in the background.")
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

    def open_detached_tcw(self, _event=None):
        assert gc.ex_tcw is not None
        gc.ex_tcw.show()

    def open_detached_tlw(self, _event=None):
        assert gc.ex_tlw is not None
        gc.ex_tlw.show()

    # ------------------ Functions ------------------
    # error
    def errorNotif(self, err: str):
        native_notify("Unexpected Error!", err)

    def copy_tb(self, theType: Literal["transcribed", "translated"]):
        tb_dict = {"transcribed": self.tb_transcribed, "translated": self.tb_translated}

        self.root.clipboard_clear()
        self.root.clipboard_append(tb_dict[theType].get("1.0", "end"))
        self.root.update()

        self.btn_copy.configure(text="Copied!")

        # reset after .7 second
        self.root.after(700, lambda: self.btn_copy.configure(text="Copy"))

    # on start
    def on_init(self):
        if system() != "Windows":
            self.radio_speaker.configure(state="disabled")

        # update on start
        self.mode_change()
        self.cb_input_device_init()
        self.cb_engine_change(sj.cache["tl_engine"])

        windows_os_only([self.radio_speaker, self.cb_speaker, self.lbl_speaker, self.btn_config_speaker])

        def first_open():
            if mbox(
                "Hello! :)", "Welcome to Speech Translate!\n\nIt seems like this is your first time using the app."
                " Would you like to open the documentation to learn more about the app?"
                "\n\n*You can also open it later from the help menu.", 3, self.root
            ):
                OpenUrl("https://github.com/Dadangdut33/Speech-Translate/wiki")
            sj.save_key("first_open", False)

        if sj.cache["first_open"]:
            self.root.after(100, first_open)

        # check ffmpeg
        gc.has_ffmpeg = check_ffmpeg_in_path()[0]
        self.root.after(2000, self.check_ffmpeg, gc.has_ffmpeg)

    def check_ffmpeg(self, has_ffmpeg: bool):
        ffmpeg_installed = False
        user_cancel = False
        if not has_ffmpeg:
            # prompt to install ffmpeg
            if mbox(
                "FFmpeg is not found in your system path!",
                "FFmpeg is essential for the app to work properly.\n\nDo you want to install it now?",
                3,
            ):
                success, msg = install_ffmpeg()
                if not success:
                    mbox("Error", msg, 2)

                if check_ffmpeg_in_path()[0]:
                    gc.has_ffmpeg = True
                    ffmpeg_installed = success
                else:
                    ffmpeg_installed = False
            else:
                ffmpeg_installed = False
                user_cancel = True
        else:
            ffmpeg_installed = True

        return ffmpeg_installed, user_cancel

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

        menu = Menu(self.btn_config_hostAPI, tearoff=0)
        menu.add_command(label="Refresh", command=refreshDict[theType])
        menu.add_command(label="Set to default", command=setDefaultDict[theType])

        success, default_host = getDefaultDict[theType]()
        if success:
            assert isinstance(default_host, Dict)
            menu.add_separator()
            menu.add_command(label=f"Default: {default_host['name']}", state="disabled")

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

            self.cb_mic.set("[WARNING] No default mic found")
        else:
            assert isinstance(default_device, Dict)
            found = False
            index = 0
            for i, name in enumerate(self.cb_mic["values"]):
                if similar(default_device["name"], name) > 0.6:
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

            self.cb_speaker.set("[WARNING] No default speaker found")
        else:
            assert isinstance(default_device, Dict)
            found = False
            index = 0
            for i, name in enumerate(self.cb_speaker["values"]):
                if similar(default_device["name"], name) > 0.6:
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
        # check if engine is whisper and currently in translate only mode
        # if yes, will make the transcribe model combobox disabled
        if _event in model_keys and "selected" in self.cbtn_task_translate.state(
        ) and "selected" not in self.cbtn_task_transcribe.state():
            self.cb_source_lang["values"] = engine_select_source_dict[self.cb_engine.get()]
            self.cb_model.configure(state="disabled")
        else:
            self.cb_source_lang["values"] = engine_select_source_dict[self.cb_model.get()]
            self.cb_model.configure(state="readonly")

        # Then update the target cb list with checks
        self.cb_target_lang["values"] = engine_select_target_dict[self.cb_engine.get()]

        # check if the target lang is not in the new list
        if self.cb_target_lang.get() not in self.cb_target_lang["values"]:
            self.cb_target_lang.current(0)

        # check if the source lang is not in the new list
        if self.cb_source_lang.get() not in self.cb_source_lang["values"]:
            self.cb_source_lang.current(0)

        # save
        sj.save_key("sourceLang", self.cb_source_lang.get())
        sj.save_key("targetLang", self.cb_target_lang.get())

        if _event:
            sj.save_key("tl_engine", _event)

    # clear textboxes
    def tb_clear(self):
        gc.clear_all()

    # Swap textboxes
    def tb_swap_content(self):
        gc.swap_textbox()

    # swap select language and textbox
    def cb_swap_lang(self):
        # swap lang
        tmpTarget = self.cb_target_lang.get()
        tmpSource = self.cb_source_lang.get()
        self.cb_source_lang.set(tmpTarget)
        self.cb_target_lang.set(tmpSource)

        if self.cb_target_lang.get() == "Auto detect":
            self.cb_target_lang.current(0)

        # save
        sj.save_key("sourceLang", self.cb_source_lang.get())
        sj.save_key("targetLang", self.cb_target_lang.get())

        # swap text only if mode is transcribe and translate
        # if "selected" in self.cbtn_task_transcribe.state() and "selected" in self.cbtn_task_translate.state():
        gc.swap_textbox()

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

            self.cb_source_lang.configure(state="readonly")
            self.cb_target_lang.configure(state="readonly")
            self.cb_engine.configure(state="readonly")
            self.cb_model.configure(state="readonly")
            self.enable_rec()

        elif "selected" in self.cbtn_task_transcribe.state() and "selected" not in self.cbtn_task_translate.state():
            # transcribe only
            self.tb_transcribed_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_transcribed.pack(fill="both", expand=True, padx=1, pady=1)

            self.tb_translated_bg.pack_forget()
            self.tb_translated.pack_forget()

            self.cb_source_lang.configure(state="readonly")
            self.cb_target_lang.configure(state="disabled")
            self.cb_engine.configure(state="disabled")
            self.cb_model.configure(state="readonly")
            self.enable_rec()

        elif "selected" not in self.cbtn_task_transcribe.state() and "selected" in self.cbtn_task_translate.state():
            # translate only
            self.tb_transcribed_bg.pack_forget()
            self.tb_transcribed.pack_forget()

            self.tb_translated_bg.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.tb_translated.pack(fill="both", expand=True, padx=1, pady=1)

            self.cb_source_lang.configure(state="readonly")
            self.cb_target_lang.configure(state="readonly")
            self.cb_engine.configure(state="readonly")
            self.cb_model.configure(state="readonly")
            self.enable_rec()

        else:  # both not selected
            self.cb_source_lang.configure(state="disabled")
            self.cb_target_lang.configure(state="disabled")
            self.cb_engine.configure(state="disabled")
            self.cb_model.configure(state="disabled")
            self.disable_rec()

    def disable_rec(self):
        self.btn_record.configure(state="disabled")
        self.tb_transcribed.configure(state="disabled")
        self.tb_translated.configure(state="disabled")

    def enable_rec(self):
        self.btn_record.configure(state="normal")
        self.tb_transcribed.configure(state="normal")
        self.tb_translated.configure(state="normal")

    def disable_interactions(self):
        self.cbtn_task_transcribe.configure(state="disabled")
        self.cbtn_task_translate.configure(state="disabled")
        self.cb_hostAPI.configure(state="disabled")
        self.cb_mic.configure(state="disabled")
        self.cb_speaker.configure(state="disabled")
        self.btn_swap.configure(state="disabled")
        self.btn_record.configure(state="disabled")
        self.btn_import_file.configure(state="disabled")
        self.btn_tool.configure(state="disabled")
        self.cb_model.configure(state="disabled")
        self.cb_engine.configure(state="disabled")
        self.cb_source_lang.configure(state="disabled")
        self.cb_target_lang.configure(state="disabled")
        self.radio_mic.configure(state="disabled")
        self.radio_speaker.configure(state="disabled")

    def enable_interactions(self):
        self.cbtn_task_transcribe.configure(state="normal")
        self.cbtn_task_translate.configure(state="normal")
        self.cb_hostAPI.configure(state="readonly")
        self.cb_mic.configure(state="readonly")
        self.cb_speaker.configure(state="readonly")
        self.btn_swap.configure(state="normal")
        self.btn_record.configure(state="normal")
        self.btn_import_file.configure(state="normal")
        self.btn_tool.configure(state="normal")
        self.cb_model.configure(state="readonly")
        self.cb_engine.configure(state="readonly")
        self.radio_mic.configure(state="normal")
        self.radio_speaker.configure(state="normal")
        self.cb_source_lang.configure(state="readonly")

        if self.cb_engine.get() in model_keys and "selected" in self.cbtn_task_translate.state(
        ) and "selected" not in self.cbtn_task_transcribe.state():
            self.cb_model.configure(state="disabled")
        else:
            self.cb_model.configure(state="readonly")
        if "selected" not in self.cbtn_task_translate.state():
            self.cb_target_lang.configure(state="disabled")
        else:
            self.cb_target_lang.configure(state="readonly")

    def start_loadBar(self):
        self.loadBar.configure(mode="indeterminate")
        self.loadBar.start(15)

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
            self.cb_source_lang.get().lower(),
            self.cb_target_lang.get().lower(),
            self.cb_mic.get(),
            self.cb_speaker.get(),
        )

    # ------------------ Export ------------------
    def export_rec(self, mode: Literal["Transcribe", "Translate"]):
        fileName = f"{mode}d {strftime('%Y-%m-%d %H-%M-%S')}"
        text = str(self.tb_transcribed.get(1.0, "end")) if mode == "Transcribe" else str(self.tb_translated.get(1.0, "end"))
        results = gc.tc_sentences if mode == "Transcribe" else gc.tl_sentences

        # check types. If results contains str that means export is only .txt
        if not any(isinstance(res, str) for res in results):
            valid_types = (
                ("Text File", "*.txt"), ("SubRip Subtitle (SRT)", "*.srt"), ("Advanced Substation Alpha (ASS)", "*.ass"),
                ("Video Text to Track (VTT)", "*.vtt"), ("JavaScript Object Notation (JSON)", "*.json"),
                ("Tab Separated Values (TSV)", "*.tsv"), ("Comma Separated Values (CSV)", "*.csv")
            )
        else:
            valid_types = (("Text File", "*.txt"), )

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=fileName,
            filetypes=valid_types,
            title=f"Select Format to Export {mode}d text From Record",
            confirmoverwrite=True
        )

        if len(file_path) == 0:  # cancel
            return

        f_name, f_ext = os.path.splitext(file_path)

        if "txt" in f_ext:
            logger.debug(f"Exporting {mode}d text to {file_path}")
            # open file write it
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
        else:
            index = 1
            for res in results:
                assert isinstance(res, WhisperResult), "Error result should be a WhisperResult, this should not happened"

                # if index > 1 then add _2 etc..
                save_name = f"{f_name}_{index}" if index > 1 else f_name
                logger.debug(f"Exporting {mode}d text to {save_name}")

                save_output_stable_ts(res, save_name, [f_ext.replace(".", "")], sj)
                index += 1

        # open folder
        open_folder(file_path)

    def export_result(self):
        # check based on mode
        if "selected" in self.cbtn_task_transcribe.state() and "selected" not in self.cbtn_task_translate.state():
            text = str(self.tb_transcribed.get(1.0, "end"))

            if len(text.strip()) == 0:
                mbox("Could not export!", "No text to export", 1)
                return

            self.export_rec("Transcribe")
        elif "selected" not in self.cbtn_task_transcribe.state() and "selected" in self.cbtn_task_translate.state():
            text = str(self.tb_translated.get(1.0, "end"))

            if len(text.strip()) == 0:
                mbox("Could not export!", "No text to export", 1)
                return

            self.export_rec("Translate")
        elif "selected" in self.cbtn_task_transcribe.state() and "selected" in self.cbtn_task_translate.state():
            if self.prompting:
                return

            self.prompting = True
            picked = prompt_with_choices(
                self.root, "Choose Result to Export", "Which result do you wish to export?",
                ["Transcribe", "Translate", "Both Transcribe and Translate"]
            )
            self.prompting = False

            if picked is None:
                return

            if "Transcribe" in picked:
                text = str(self.tb_transcribed.get(1.0, "end"))

                if len(text.strip()) == 0:
                    mbox("Could not export Transcribed text!", "No text to export", 1)
                else:
                    self.export_rec("Transcribe")

            if "Translate" in picked:
                text = str(self.tb_translated.get(1.0, "end"))

                if len(text.strip()) == 0:
                    mbox("Could not export Translated text!", "No text to export", 1)
                else:
                    self.export_rec("Translate")

    def model_dl_cancel(self):
        if not mbox("Cancel confirmation", "Are you sure you want to cancel downloading?", 3, self.root):
            return

        gc.cancel_dl = True  # Raise flag to stop

    def after_model_dl(self, taskname, task):
        # ask if user wants to continue using the model
        if mbox("Model is now Ready!", f"Continue task? ({taskname})", 3, self.root):
            task()

    def destroy_transient_toplevel(self, name, similar=False):
        for child in self.root.winfo_children():
            if isinstance(child, Toplevel):
                if child.title() == name:
                    child.destroy()
                    break
                if similar and name in child.title():
                    child.destroy()
                    break

    def check_model(self, key, is_english, taskname, task):
        try:
            # check model first
            model_name = append_dot_en(key, is_english)
            use_faster_whisper = sj.cache["use_faster_whisper"]
            extramsg = "\n\n*Once started, you cannot cancel or pause the download for downloading faster whisper model." if use_faster_whisper else "\n\n*Once started, you can cancel or pause the download anytime you want."

            model_dir = sj.cache["dir_model"] if sj.cache["dir_model"] != "auto" else get_default_download_root()
            if use_faster_whisper and model_name != "large-v3":
                ok = verify_model_faster_whisper(model_name, model_dir)
            else:
                if model_name == "large-v3":
                    logger.warning("large-v3 is not available on faster whisper yet, using whisper instead")
                ok = verify_model_whisper(model_name, model_dir)

            if not ok:
                if mbox(
                    "Model is not downloaded yet!",
                    f"`{model_name + '` Whisper'  if not use_faster_whisper else model_name + '` Faster Whisper'} Model not found! You will need to download it first!\n\nDo you want to download it now?{extramsg}",
                    3,
                    self.root,
                ):
                    # if true will download the model, after that, the function will run after_func if successfull
                    logger.info("Downloading model...")
                    try:
                        kwargs = {
                            "after_func": lambda: self.after_model_dl(taskname, task),
                            "use_faster_whisper": use_faster_whisper
                        }

                        if not use_faster_whisper:
                            kwargs["cancel_func"] = self.model_dl_cancel

                        if sj.cache["dir_model"] != "auto":
                            kwargs = {"download_root": sj.cache["dir_model"]}

                        gc.dl_thread = Thread(
                            target=download_model,
                            args=(model_name, self.root),
                            kwargs=kwargs,
                            daemon=True,
                        )
                        gc.dl_thread.start()
                    except Exception as e:
                        logger.exception(e)
                        self.errorNotif(str(e))

                # return false to stop previous task regardless of the answer
                return False, ""
            return True, model_name
        except Exception as e:
            logger.exception(e)
            self.errorNotif(str(e))
            return False, ""

    # ------------------ Rec ------------------
    def rec(self):
        is_speaker = "selected" in self.radio_speaker.state()
        if is_speaker and system() != "Windows":  # double checking. Speaker input is only available on Windows
            mbox(
                "Not available",
                "This feature is only available on Windows."
                "\n\nIn order to record PC sound from OS other than Windows you will need to create a virtual audio loopback"
                " to pass the speaker output as an input. You can use software like PulseAudio or Blackhole to do this."
                "\n\nAfter that you can change your default input device to the virtual audio loopback.",
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
        tc, tl, m_key, engine, source, target, mic, speaker = self.get_args()
        if source == target and tl:
            mbox("Invalid options!", "Source and target language cannot be the same", 2)
            return

        # check model first
        status, model_tc = self.check_model(m_key, source == "english", "mic record", self.rec)
        if not status:
            return

        if engine in model_keys and tl:
            status, engine = self.check_model(engine, source == "english", "recording", self.rec)
            if not status:
                return

        # check ffmpeg
        success, user_cancel = self.check_ffmpeg(check_ffmpeg_in_path()[0])
        if not success:
            # ask if user want to continue processing
            if not mbox(
                "FFMpeg is not installed!",
                "The program needs ffmpeg to process files and will probably not work without it. Do you still want to continue regardless of it?",
                3, self.root
            ):
                return

        if user_cancel:
            mbox(
                "Cancelled",
                "The program needs ffmpeg to process files and will probably not work without it. Please install it first.",
                2,
            )

            return

        # ui changes
        self.tb_clear()
        self.start_loadBar()
        self.disable_interactions()
        self.btn_record.configure(text="Loading", command=self.rec_stop, state="normal")

        gc.enable_rec()  # Flag update    # Disable recording is by button input

        # Start thread
        try:
            device = mic if not is_speaker else speaker
            recThread = Thread(
                target=record_session,
                args=(source, target, engine, model_tc, device, tc, tl, is_speaker),
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
        gc.disable_rec()

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

        def do_process(m_key, engine, source, target, tc, tl, files):
            # lang is lowered when send from FileImportDialog
            if source == target and tl:
                mbox("Invalid options!", "Source and target language cannot be the same", 2)
                return False

            # check model first
            status, model_tc = self.check_model(m_key, source == "english", "file import", self.import_file)
            if not status:
                return False

            if engine in model_keys and tl:
                status, engine = self.check_model(engine, source == "english", "file import", self.import_file)
                if not status:
                    return False

            # check ffmpeg
            success, user_cancel = self.check_ffmpeg(check_ffmpeg_in_path()[0])
            if not success:
                # ask if user want to continue processing
                if not mbox(
                    "FFMpeg is not installed!",
                    "The program needs ffmpeg to process files and will probably not work without it. Do you still want to continue regardless of it?",
                    3, self.root
                ):
                    return False

            if user_cancel:
                mbox(
                    "Cancelled",
                    "The program needs ffmpeg to process files and will probably not work without it. Please install it first.",
                    2,
                )

                return False

            # ui changes
            self.tb_clear()
            self.start_loadBar()
            self.disable_interactions()
            self.btn_import_file.configure(text="Loading", command=lambda: self.from_file_stop(True), state="normal")

            gc.enable_file_process()  # Flag update

            # Start thread
            try:
                recFileThread = Thread(
                    target=process_file, args=(list(files), model_tc, source, target, tc, tl, engine), daemon=True
                )
                recFileThread.start()

                return True
            except Exception as e:
                logger.exception(e)
                self.errorNotif(str(e))
                self.from_file_stop()

                return False

        tc, tl, m_key, engine, source, target, _mic, _speaker = self.get_args()
        kwargs = {
            "set_cb_model": m_key,
            "set_cb_engine": engine,
            "set_cb_source_lang": up_first_case(source),
            "set_cb_target_lang": up_first_case(target),
            "set_task_transcribe": tc,
            "set_task_translate": tl,
        }

        self.disable_interactions()
        prompt = FileImportDialog(self.root, "Import Files", do_process, sj.cache["theme"], **kwargs)
        self.root.wait_window(prompt.root)  # wait for the prompt to close
        self.enable_interactions()

    def from_file_stop(self, prompt=False, notify=True, master=None):
        if prompt:
            if not mbox(
                "Confirm", "Are you sure you want to cancel the file transcribe/translate process?", 3,
                self.root if master is None else master
            ):
                return

        logger.info("Cancelling file import processing...")
        gc.disable_file_process()
        gc.disable_tc()
        gc.disable_tl()
        self.destroy_transient_toplevel("File Import Progress")

        if notify:
            mbox(
                "Cancelled",
                f"Cancelled file import processing\n\nTranscribed {gc.file_tced_counter} "
                f"and translated {gc.file_tled_counter} file",
                0,
                self.root,
            )

        self.loadBar.stop()
        self.loadBar.configure(mode="determinate")
        self.btn_import_file.configure(text="Import file", command=self.import_file)
        self.enable_interactions()

    def refine_file(self):
        if gc.dl_thread and gc.dl_thread.is_alive():
            mbox(
                "Please wait! A model is being downloaded",
                "A Model is still being downloaded! Please wait until it finishes first!",
                1,
            )
            return

        def do_process(m_key, files):
            # check model first
            status, model_tc = self.check_model(m_key, False, "file refinement", self.refine_file)
            if not status:
                return False

            # check ffmpeg
            success, user_cancel = self.check_ffmpeg(check_ffmpeg_in_path()[0])
            if not success:
                # ask if user want to continue processing
                if not mbox(
                    "FFMpeg is not installed!",
                    "The program needs ffmpeg to process files and will probably not work without it. Do you still want to continue regardless of it?",
                    3, self.root
                ):
                    return False

            if user_cancel:
                mbox(
                    "Cancelled",
                    "The program needs ffmpeg to process files and will probably not work without it. Please install it first.",
                    2,
                )

                return False

            # ui changes
            self.tb_clear()
            self.start_loadBar()
            self.disable_interactions()

            gc.enable_file_process()  # Flag update

            # Start thread
            try:
                refineThread = Thread(target=mod_result, args=(files, model_tc, "refinement"), daemon=True)
                refineThread.start()

                return True
            except Exception as e:
                logger.exception(e)
                self.errorNotif(str(e))
                self.refinement_stop()

                return False

        tc, tl, m_key, engine, source, target, _mic, _speaker = self.get_args()
        kwargs = {"set_cb_model": m_key}
        self.disable_interactions()
        prompt = RefinementDialog(self.root, "Refine Result", do_process, sj.cache["theme"], **kwargs)
        self.root.wait_window(prompt.root)  # wait for the prompt to close
        self.enable_interactions()

    def refinement_stop(self, prompt=False, notify=True, master=None):
        if prompt:
            if not mbox(
                "Confirm", "Are you sure you want to cancel the refinement process?", 3,
                self.root if master is None else master
            ):
                return

        logger.info("Cancelling refinement...")
        gc.disable_file_process()

        if notify:
            mbox(
                "Cancelled",
                f"Cancelled refinement process\n\nRefined {gc.mod_file_counter} file",
                0,
                self.root,
            )

        self.loadBar.stop()
        self.loadBar.configure(mode="determinate")
        self.enable_interactions()

    def align_file(self):
        if gc.dl_thread and gc.dl_thread.is_alive():
            mbox(
                "Please wait! A model is being downloaded",
                "A Model is still being downloaded! Please wait until it finishes first!",
                1,
            )
            return

        def do_process(m_key, files):
            # check model first
            status, model_tc = self.check_model(m_key, False, "file alignment", self.align_file)
            if not status:
                return False

            # check ffmpeg
            success, user_cancel = self.check_ffmpeg(check_ffmpeg_in_path()[0])
            if not success:
                # ask if user want to continue processing
                if not mbox(
                    "FFMpeg is not installed!",
                    "The program needs ffmpeg to process files and will probably not work without it. Do you still want to continue regardless of it?",
                    3, self.root
                ):
                    return False

            if user_cancel:
                mbox(
                    "Cancelled",
                    "The program needs ffmpeg to process files and will probably not work without it. Please install it first.",
                    2,
                )

                return False

            # ui changes
            self.tb_clear()
            self.start_loadBar()
            self.disable_interactions()

            gc.enable_file_process()  # Flag update

            # Start thread
            try:
                alignThread = Thread(target=mod_result, args=(files, model_tc, "alignment"), daemon=True)
                alignThread.start()

                return True
            except Exception as e:
                logger.exception(e)
                self.errorNotif(str(e))
                self.alignment_stop()

                return False

        tc, tl, m_key, engine, source, target, _mic, _speaker = self.get_args()
        kwargs = {"set_cb_model": m_key}
        self.disable_interactions()
        prompt = AlignmentDialog(self.root, "Align Result", do_process, sj.cache["theme"], **kwargs)
        self.root.wait_window(prompt.root)  # wait for the prompt to close
        self.enable_interactions()

    def alignment_stop(self, prompt=False, notify=True, master=None):
        if prompt:
            if not mbox(
                "Confirm", "Are you sure you want to cancel the alignment process?", 3,
                self.root if master is None else master
            ):
                return

        logger.info("Cancelling alignment...")
        gc.disable_file_process()

        if notify:
            mbox(
                "Cancelled",
                f"Cancelled alignment process\n\nAligned {gc.mod_file_counter} file",
                0,
                self.root,
            )

        self.loadBar.stop()
        self.loadBar.configure(mode="determinate")
        self.enable_interactions()

    def translate_file(self):
        if gc.dl_thread and gc.dl_thread.is_alive():
            mbox(
                "Please wait! A model is being downloaded",
                "A Model is still being downloaded! Please wait until it finishes first!",
                1,
            )
            return

        def do_process(engine, lang_target, files):
            # lang is lowered when send from TranslateResultDialog
            # no check because not using any model and no need for ffmpeg
            # ui changes
            self.tb_clear()
            self.start_loadBar()
            self.disable_interactions()

            gc.enable_file_process()

            # Start thread
            try:
                translateThread = Thread(target=translate_result, args=(files, engine, lang_target), daemon=True)
                translateThread.start()

                return True
            except Exception as e:
                logger.exception(e)
                self.errorNotif(str(e))
                self.translate_stop()

                return False

        tc, tl, m_key, engine, source, target, _mic, _speaker = self.get_args()
        kwargs = {
            "set_cb_model": m_key,
            "set_cb_engine": engine,
            "set_cb_target_lang": up_first_case(target),
        }

        self.disable_interactions()
        prompt = TranslateResultDialog(self.root, "Translate Whisper Result", do_process, sj.cache["theme"], **kwargs)
        self.root.wait_window(prompt.root)  # wait for the prompt to close
        self.enable_interactions()

    def translate_stop(self, prompt=False, notify=True, master=None):
        if prompt:
            if not mbox(
                "Confirm", "Are you sure you want to cancel the result translation process?", 3,
                self.root if master is None else master
            ):
                return

        logger.info("Cancelling translation...")
        gc.disable_file_process()

        if notify:
            mbox(
                "Cancelled",
                f"Cancelled translation process\n\nTranslated {gc.mod_file_counter} file",
                0,
                self.root,
            )

        self.loadBar.stop()
        self.loadBar.configure(mode="determinate")
        self.enable_interactions()


def get_gpu_info():
    result = ""
    try:
        gpu_count = cuda.device_count()
        if gpu_count == 0:
            result = "No GPU detected"
        elif gpu_count == 1:
            result = cuda.get_device_name(0)
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
        if not cuda.is_available():
            result = "CUDA is not available! Using CPU instead"
        else:
            count = cuda.device_count()
            gpus = [cuda.get_device_name(i) for i in range(count)]
            result = f"Using {count} GPU(s): {', '.join(gpus)}"
    except Exception as e:
        logger.exception(e)
        result = "CUDA fail to check! Failed to detect GPU"
    finally:
        return result


def main(with_log_init=True):
    if with_log_init:
        init_logging(sj.cache["log_level"])
    logger.info(f"App Version: {__version__}")
    logger.info(f"OS: {system()} {release()} {version()} | CPU: {processor()}")
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
