import os
import platform
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font, colorchooser
from multiprocessing import Process

# User defined
from speech_translate.Globals import app_icon, app_name, fJson, gClass, dir_log, dir_temp
from speech_translate.Logging import logger, current_log
from speech_translate.utils.DownloadModel import verify_model, download_model, get_default_download_root
from speech_translate.utils.Json import default_setting
from speech_translate.utils.Helper import startFile
from .MBox import Mbox
from .Tooltip import CreateToolTip


def chooseColor(theWidget, initialColor, parent):
    color = colorchooser.askcolor(initialcolor=initialColor, title="Choose a color", parent=parent)
    if color[1] is not None:
        theWidget.delete(0, tk.END)
        theWidget.insert(0, color[1])


class SettingWindow:
    """
    Setting UI
    """

    def __init__(self):
        self.root = tk.Tk()

        self.root.title(app_name)
        self.root.geometry("950x370")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.wm_attributes("-topmost", False)  # Default False

        self.fonts = list(font.families())
        self.fonts.append("TKDefaultFont")
        self.fonts.sort()

        # ------------------ Frames ------------------
        self.frame_top = tk.Frame(self.root)
        self.frame_top.pack(side=tk.TOP, fill=tk.X)

        self.frame_bottom = tk.Frame(self.root)
        self.frame_bottom.pack(side=tk.BOTTOM, fill=tk.X)

        # ------------------ Widgets ------------------
        # notebook
        self.tabControl = ttk.Notebook(self.frame_top)
        self.tabControl.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.ft1 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft1, text="General")

        self.ft2 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft2, text="Translation")

        self.ft3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft3, text="Textbox")

        self.ft4 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft4, text="Other")

        # ------------------ Widgets - General ------------------
        self.lf_t1r1 = tk.LabelFrame(self.ft1, text="• Audio Capture")
        self.lf_t1r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # cutoff
        # 1
        self.t1r1_1 = ttk.Frame(self.lf_t1r1)
        self.t1r1_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.lbl_cutOff_mic = ttk.Label(self.t1r1_1, text="Mic Cutoff: ")
        self.lbl_cutOff_mic.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_cutOff_mic, "Set the cut off length (in seconds) for microphone input.")

        self.spn_cutOff_mic = ttk.Spinbox(
            self.t1r1_1,
            from_=3,
            to=30,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("cutOff_mic", int(self.spn_cutOff_mic.get())),
        )
        self.spn_cutOff_mic.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(self.spn_cutOff_mic, 3, 30, lambda: fJson.savePartialSetting("cutOff_mic", int(self.spn_cutOff_mic.get()))),
        )
        self.spn_cutOff_mic.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spn_cutOff_mic, "Set the cut off length (in seconds) for microphone input.")

        self.lbl_cutOff_speaker = ttk.Label(self.t1r1_1, text="Speaker Cutoff: ")
        self.lbl_cutOff_speaker.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_cutOff_speaker, "Set the cut off length (in seconds) for speaker input.")

        self.spn_cutOff_speaker = ttk.Spinbox(
            self.t1r1_1,
            from_=3,
            to=30,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("cutOff_speaker", int(self.spn_cutOff_speaker.get())),
        )
        self.spn_cutOff_speaker.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(self.spn_cutOff_speaker, 3, 30, lambda: fJson.savePartialSetting("cutOff_speaker", int(self.spn_cutOff_speaker.get()))),
        )
        self.spn_cutOff_speaker.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spn_cutOff_speaker, "Set the cut off length (in seconds) for speaker input.")

        # 2
        self.t1r1_2 = ttk.Frame(self.lf_t1r1)
        self.t1r1_2.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.lbl_separate_text_with = ttk.Label(self.t1r1_2, text="Text Separator: ")
        self.lbl_separate_text_with.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_separate_text_with, "Set the separator for text that is transcribed/translated.\n\n. - Default value \\n", wrapLength=400)

        self.entry_separate_text_with = ttk.Entry(self.t1r1_2)
        self.entry_separate_text_with.pack(side=tk.LEFT, padx=5)
        self.entry_separate_text_with.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("separate_with", self.entry_separate_text_with.get()))
        CreateToolTip(self.entry_separate_text_with, "Set the separator for text that is transcribed/translated.\n\nDefault value \\n", wrapLength=400)

        # 3
        self.t1r1_3 = ttk.Frame(self.lf_t1r1)
        self.t1r1_3.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.lbl_max_temp = ttk.Label(self.t1r1_3, text="Max Temp File: ")
        self.lbl_max_temp.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_max_temp, "Set max number of audio temp files before deletion in each recording session")

        self.spn_max_temp = ttk.Spinbox(
            self.t1r1_3, from_=10, to=500, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: fJson.savePartialSetting("max_temp", int(self.spn_max_temp.get()))
        )
        self.spn_max_temp.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_max_temp, 10, 500, lambda: fJson.savePartialSetting("max_temp", int(self.spn_max_temp.get()))))
        self.spn_max_temp.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spn_max_temp, "Set max number of audio temp files before deletion in each recording session")

        self.cbtn_keep_audio = ttk.Checkbutton(self.t1r1_3, text="Keep Audio", command=lambda: fJson.savePartialSetting("keep_audio", self.cbtn_keep_audio.instate(["selected"])))
        self.cbtn_keep_audio.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.cbtn_keep_audio, "Keep audio files after transcription/translation")

        # log
        self.lf_t1r2 = tk.LabelFrame(self.ft1, text="• Logging")
        self.lf_t1r2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t1_r2_1 = ttk.Frame(self.lf_t1r2)
        self.t1_r2_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.lbl_log_location = ttk.Label(self.t1_r2_1, text="Log Files Location ", width=16)
        self.lbl_log_location.pack(side=tk.LEFT, padx=5)

        self.entry_log_location_value = ttk.Entry(self.t1_r2_1, cursor="hand2", width=100)
        self.entry_log_location_value.insert(0, dir_log)
        self.entry_log_location_value.config(state="readonly")
        self.entry_log_location_value.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_log_location_value.bind("<Button-1>", lambda e: startFile(dir_log))
        self.entry_log_location_value.bind("<Button-3>", lambda e: self.promptDeleteLog())
        CreateToolTip(self.entry_log_location_value, "Location of log file.\n- LClick to open the folder.\n- RClick to delete all log files.")

        self.t1_r2_2 = ttk.Frame(self.lf_t1r2)
        self.t1_r2_2.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.cbtn_keep_log = ttk.Checkbutton(self.t1_r2_2, text="Keep Log Files", command=lambda: fJson.savePartialSetting("keep_log", self.cbtn_keep_log.instate(["selected"])))
        self.cbtn_keep_log.pack(side=tk.LEFT, padx=5, pady=5)

        self.cbtn_verbose = ttk.Checkbutton(self.t1_r2_2, text="Verbose Logging for Whisper", command=lambda: fJson.savePartialSetting("verbose", self.cbtn_verbose.instate(["selected"])))
        self.cbtn_verbose.pack(side=tk.LEFT, padx=5)

        # only on windows
        if platform.system() == "Windows":
            self.cbtn_hide_console_window_on_start = ttk.Checkbutton(
                self.t1_r2_2, text="Hide Console Window on Start", command=lambda: fJson.savePartialSetting("hide_console_window_on_start", self.cbtn_hide_console_window_on_start.instate(["selected"]))
            )
            self.cbtn_hide_console_window_on_start.pack(side=tk.LEFT, padx=5)
            CreateToolTip(self.cbtn_hide_console_window_on_start, "Will hide console (log) window every program start. Only on Windows.")

        # model
        self.lf_t1r3 = tk.LabelFrame(self.ft1, text="• Model")
        self.lf_t1r3.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # label model location
        self.t1_r3_1 = ttk.Frame(self.lf_t1r3)
        self.t1_r3_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.lbl_model_location = ttk.Label(self.t1_r3_1, text="Model Location ", width=16)
        self.lbl_model_location.pack(side=tk.LEFT, padx=5)

        self.entry_model_location_value = ttk.Entry(self.t1_r3_1, cursor="hand2", width=100)
        self.entry_model_location_value.insert(0, get_default_download_root())
        self.entry_model_location_value.config(state="readonly")
        self.entry_model_location_value.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_model_location_value.bind("<Button-1>", lambda e: startFile(self.entry_model_location_value.cget("text")))
        CreateToolTip(self.entry_model_location_value, "Location of the model file.\nLClick to open the folder")

        # the models
        self.t1r3_2 = ttk.Frame(self.lf_t1r3)
        self.t1r3_2.pack(side=tk.TOP, fill=tk.X)

        # small
        self.t1r3_p1 = ttk.Frame(self.t1r3_2)
        self.t1r3_p1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_tiny = ttk.LabelFrame(self.t1r3_p1, text="Tiny")
        self.lf_model_tiny.pack(side=tk.LEFT)

        self.btn_interact_tiny = ttk.Button(self.lf_model_tiny, text="Verify", command=lambda: self.model_check("tiny", self.btn_interact_tiny))
        self.btn_interact_tiny.pack(side=tk.LEFT, padx=5)

        # small en
        self.t1r3_p2 = ttk.Frame(self.t1r3_2)
        self.t1r3_p2.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_tiny_eng = ttk.LabelFrame(self.t1r3_p2, text="Tiny (en)")
        self.lf_model_tiny_eng.pack(side=tk.LEFT)

        self.btn_interact_tiny_eng = ttk.Button(self.lf_model_tiny_eng, text="Verify", command=lambda: self.model_check("tiny.en", self.btn_interact_tiny_eng))
        self.btn_interact_tiny_eng.pack(side=tk.LEFT, padx=5)

        # base
        self.t1r3_p3 = ttk.Frame(self.t1r3_2)
        self.t1r3_p3.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_base = ttk.LabelFrame(self.t1r3_p3, text="Base")
        self.lf_model_base.pack(side=tk.LEFT)

        self.btn_interact_base = ttk.Button(self.lf_model_base, text="Verify", command=lambda: self.model_check("base", self.btn_interact_base))
        self.btn_interact_base.pack(side=tk.LEFT, padx=5)

        # base en
        self.t1r3_p4 = ttk.Frame(self.t1r3_2)
        self.t1r3_p4.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_base_eng = ttk.LabelFrame(self.t1r3_p4, text="Base (en)")
        self.lf_model_base_eng.pack(side=tk.LEFT)

        self.btn_interact_base_eng = ttk.Button(self.lf_model_base_eng, text="Verify", command=lambda: self.model_check("base.en", self.btn_interact_base_eng))
        self.btn_interact_base_eng.pack(side=tk.LEFT, padx=5)

        # small
        self.t1r3_p5 = ttk.Frame(self.t1r3_2)
        self.t1r3_p5.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_small = ttk.LabelFrame(self.t1r3_p5, text="Small")
        self.lf_model_small.pack(side=tk.LEFT)

        self.btn_interact_small = ttk.Button(self.lf_model_small, text="Verify", command=lambda: self.model_check("small", self.btn_interact_small))
        self.btn_interact_small.pack(side=tk.LEFT, padx=5)

        # small en
        self.t1r3_p6 = ttk.Frame(self.t1r3_2)
        self.t1r3_p6.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_small_eng = ttk.LabelFrame(self.t1r3_p6, text="Small (en)")
        self.lf_model_small_eng.pack(side=tk.LEFT)

        self.btn_interact_small_eng = ttk.Button(self.lf_model_small_eng, text="Verify", command=lambda: self.model_check("small.en", self.btn_interact_small_eng))
        self.btn_interact_small_eng.pack(side=tk.LEFT, padx=5)

        # medium
        self.t1r3_p7 = ttk.Frame(self.t1r3_2)
        self.t1r3_p7.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_medium = ttk.LabelFrame(self.t1r3_p7, text="Medium")
        self.lf_model_medium.pack(side=tk.LEFT)

        self.btn_interact_medium = ttk.Button(self.lf_model_medium, text="Verify", command=lambda: self.model_check("medium", self.btn_interact_medium))
        self.btn_interact_medium.pack(side=tk.LEFT, padx=5)

        # medium en
        self.t1r3_p8 = ttk.Frame(self.t1r3_2)
        self.t1r3_p8.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_medium_eng = ttk.LabelFrame(self.t1r3_p8, text="Medium (en)")
        self.lf_model_medium_eng.pack(side=tk.LEFT)

        self.btn_interact_medium_eng = ttk.Button(self.lf_model_medium_eng, text="Verify", command=lambda: self.model_check("medium.en", self.btn_interact_medium_eng))
        self.btn_interact_medium_eng.pack(side=tk.LEFT, padx=5)

        # large
        self.t1r3_p9 = ttk.Frame(self.t1r3_2)
        self.t1r3_p9.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_large = ttk.LabelFrame(self.t1r3_p9, text="Large")
        self.lf_model_large.pack(side=tk.LEFT)

        self.btn_interact_large = ttk.Button(self.lf_model_large, text="Verify", command=lambda: self.model_check("large", self.btn_interact_large))
        self.btn_interact_large.pack(side=tk.LEFT, padx=5)

        # ------------------ Widgets - Translation ------------------
        self.lf_t3r1 = tk.LabelFrame(self.ft2, text="• Libre Translate Setting")
        self.lf_t3r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.lbl_libre_key = ttk.Label(self.lf_t3r1, text="Libre Translate API Key")
        self.lbl_libre_key.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_libre_key, "Libre Translate API Key. Leave empty if not needed or host locally.")

        self.entry_libre_key = ttk.Entry(self.lf_t3r1)
        self.entry_libre_key.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_libre_key.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_api_key", self.entry_libre_key.get()))

        self.lbl_libre_host = ttk.Label(self.lf_t3r1, text="Libre Translate Host")
        self.lbl_libre_host.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_libre_host = ttk.Entry(self.lf_t3r1)
        self.entry_libre_host.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_libre_host.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_host", self.entry_libre_host.get()))

        self.lbl_libre_port = ttk.Label(self.lf_t3r1, text="Libre Translate Port")
        self.lbl_libre_port.pack(side=tk.LEFT, padx=5, pady=5)
        self.lbl_libre_port.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_port", self.entry_libre_port.get()))

        self.entry_libre_port = ttk.Entry(self.lf_t3r1)
        self.entry_libre_port.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_libre_port.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_port", self.entry_libre_port.get()))

        self.cbtn_libre_https = ttk.Checkbutton(self.lf_t3r1, text="Use HTTPS", command=lambda: fJson.savePartialSetting("libre_https", self.cbtn_libre_https.instate(["selected"])))
        self.cbtn_libre_https.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_libre_https, "Don't use this if you're hosting locally.")

        # ------------------ Widgets - Textbox ------------------
        self.t4r1 = ttk.Frame(self.ft3)
        self.t4r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

        self.t4r2 = ttk.Frame(self.ft3)
        self.t4r2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

        self.t4r3 = ttk.Frame(self.ft3)
        self.t4r3.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

        self.t4r4 = ttk.Frame(self.ft3)
        self.t4r4.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

        self.t4r5 = ttk.Frame(self.ft3)
        self.t4r5.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=5, expand=True)

        # mw tc
        self.lbl_mw_tc = tk.LabelFrame(self.t4r1, text="• Main Window Transcribed Textbox")
        self.lbl_mw_tc.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_mw_tc_max = ttk.Label(self.lbl_mw_tc, text="Max Length")
        self.lbl_mw_tc_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_mw_tc_max, "Maximum length of the textbox. 0 = no limit.")

        self.spn_mw_tc_max = ttk.Spinbox(
            self.lbl_mw_tc,
            from_=0,
            to=10_000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("tb_mw_tc_max", int(self.spn_mw_tc_max.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_mw_tc_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_mw_tc_max, 0, 10_000, lambda: fJson.savePartialSetting("tb_mw_tc_max", int(self.spn_mw_tc_max.get()))) or self.preview_changes_tb())
        self.spn_mw_tc_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.spn_mw_tc_max, "Maximum length of the textbox. 0 = no limit.")

        self.lbl_mw_tc_font = ttk.Label(self.lbl_mw_tc, text="Font")
        self.lbl_mw_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_mw_tc_font = ttk.Combobox(self.lbl_mw_tc, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tc_font.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_mw_tc_font.bind("<<ComboboxSelected>>", lambda e: fJson.savePartialSetting("tb_mw_tc_font", self.cb_mw_tc_font.get()) or self.preview_changes_tb())

        self.lbl_mw_tc_font_size = ttk.Label(self.lbl_mw_tc, text="Font Size")
        self.lbl_mw_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spn_mw_tc_font_size = ttk.Spinbox(
            self.lbl_mw_tc,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("tb_mw_tc_font_size", int(self.spn_mw_tc_font_size.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_mw_tc_font_size.bind(
            "<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_mw_tc_font_size, 3, 120, lambda: fJson.savePartialSetting("tb_mw_tc_font_size", int(self.spn_mw_tc_font_size.get()))) or self.preview_changes_tb()
        )
        self.spn_mw_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_mw_tc_font_color = ttk.Label(self.lbl_mw_tc, text="Font Color")
        self.lbl_mw_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_font_color = ttk.Entry(self.lbl_mw_tc, width=10)
        self.entry_mw_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tc_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_mw_tc_font_color, self.entry_mw_tc_font_color.get(), self.root)
            or fJson.savePartialSetting("tb_mw_tc_font_color", self.entry_mw_tc_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_mw_tc_font_color.bind("<Key>", lambda e: "break")

        self.lbl_mw_tc_bg_color = ttk.Label(self.lbl_mw_tc, text="Background Color")
        self.lbl_mw_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_bg_color = ttk.Entry(self.lbl_mw_tc, width=10)
        self.entry_mw_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tc_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_mw_tc_bg_color, self.entry_mw_tc_bg_color.get(), self.root) or fJson.savePartialSetting("tb_mw_tc_bg_color", self.entry_mw_tc_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_mw_tc_bg_color.bind("<Key>", lambda e: "break")

        # mw tl
        self.lbl_mw_tl = tk.LabelFrame(self.t4r2, text="• Main Window Translated Textbox")
        self.lbl_mw_tl.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_mw_tl_max = ttk.Label(self.lbl_mw_tl, text="Max Length")
        self.lbl_mw_tl_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_mw_tl_max, "Maximum length of the textbox. 0 = no limit.")

        self.spn_mw_tl_max = ttk.Spinbox(
            self.lbl_mw_tl,
            from_=0,
            to=10_000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("tb_mw_tl_max", int(self.spn_mw_tl_max.get()) or self.preview_changes_tb()),
            width=10,
        )
        self.spn_mw_tl_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_mw_tl_max, 0, 10_000, lambda: fJson.savePartialSetting("tb_mw_tl_max", int(self.spn_mw_tl_max.get())) or self.preview_changes_tb()))
        self.spn_mw_tl_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.spn_mw_tl_max, "Maximum length of the textbox. 0 = no limit.")

        self.lbl_mw_tl_font = ttk.Label(self.lbl_mw_tl, text="Font")
        self.lbl_mw_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_mw_tl_font = ttk.Combobox(self.lbl_mw_tl, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tl_font.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_mw_tl_font.bind("<<ComboboxSelected>>", lambda e: fJson.savePartialSetting("tb_mw_tl_font", self.cb_mw_tl_font.get()) or self.preview_changes_tb())

        self.lbl_mw_tl_font_size = ttk.Label(self.lbl_mw_tl, text="Font Size")
        self.lbl_mw_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spn_mw_tl_font_size = ttk.Spinbox(
            self.lbl_mw_tl,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("tb_mw_tl_font_size", int(self.spn_mw_tl_font_size.get()) or self.preview_changes_tb()),
            width=10,
        )
        self.spn_mw_tl_font_size.bind(
            "<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_mw_tl_font_size, 3, 120, lambda: fJson.savePartialSetting("tb_mw_tl_font_size", int(self.spn_mw_tl_font_size.get())) or self.preview_changes_tb())
        )
        self.spn_mw_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_mw_tl_font_color = ttk.Label(self.lbl_mw_tl, text="Font Color")
        self.lbl_mw_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_font_color = ttk.Entry(self.lbl_mw_tl, width=10)
        self.entry_mw_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tl_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_mw_tl_font_color, self.entry_mw_tl_font_color.get(), self.root)
            or fJson.savePartialSetting("tb_mw_tl_font_color", self.entry_mw_tl_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_mw_tl_font_color.bind("<Key>", lambda e: "break")

        self.lbl_mw_tl_bg_color = ttk.Label(self.lbl_mw_tl, text="Background Color")
        self.lbl_mw_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_bg_color = ttk.Entry(self.lbl_mw_tl, width=10)
        self.entry_mw_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tl_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_mw_tl_bg_color, self.entry_mw_tl_bg_color.get(), self.root) or fJson.savePartialSetting("tb_mw_tl_bg_color", self.entry_mw_tl_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_mw_tl_bg_color.bind("<Key>", lambda e: "break")

        # detached tc
        self.lbl_ex_tc = tk.LabelFrame(self.t4r3, text="• Detached Transcribed Window Textbox")
        self.lbl_ex_tc.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_ex_tc_max = ttk.Label(self.lbl_ex_tc, text="Max Length")
        self.lbl_ex_tc_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_ex_tc_max, "Maximum length of the textbox. 0 = no limit.")

        self.spn_ex_tc_max = ttk.Spinbox(
            self.lbl_ex_tc,
            from_=0,
            to=10_000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("tb_ex_tc_max", int(self.spn_ex_tc_max.get()) or self.preview_changes_tb()),
            width=10,
        )
        self.spn_ex_tc_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_ex_tc_max, 0, 10_000, lambda: fJson.savePartialSetting("tb_ex_tc_max", int(self.spn_ex_tc_max.get())) or self.preview_changes_tb()))
        self.spn_ex_tc_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.spn_ex_tc_max, "Maximum length of the textbox. 0 = no limit.")

        self.lbl_ex_tc_font = ttk.Label(self.lbl_ex_tc, text="Font")
        self.lbl_ex_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_ex_tc_font = ttk.Combobox(self.lbl_ex_tc, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_ex_tc_font_size = ttk.Label(self.lbl_ex_tc, text="Font Size")
        self.lbl_ex_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spn_ex_tc_font_size = ttk.Spinbox(
            self.lbl_ex_tc,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("tb_ex_tc_font_size", int(self.spn_ex_tc_font_size.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_ex_tc_font_size.bind(
            "<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_ex_tc_font_size, 3, 120, lambda: fJson.savePartialSetting("tb_ex_tc_font_size", int(self.spn_ex_tc_font_size.get())) or self.preview_changes_tb())
        )
        self.spn_ex_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_ex_tc_font_color = ttk.Label(self.lbl_ex_tc, text="Font Color")
        self.lbl_ex_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_tc_font_color = ttk.Entry(self.lbl_ex_tc, width=10)
        self.entry_ex_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_tc_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_font_color, self.entry_ex_tc_font_color.get(), self.root)
            or fJson.savePartialSetting("tb_ex_tc_font_color", self.entry_ex_tc_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tc_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tc_bg_color = ttk.Label(self.lbl_ex_tc, text="Background Color")
        self.lbl_ex_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_tc_bg_color = ttk.Entry(self.lbl_ex_tc, width=10)
        self.entry_ex_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_tc_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_bg_color, self.entry_ex_tc_bg_color.get(), self.root) or fJson.savePartialSetting("tb_ex_tc_bg_color", self.entry_ex_tc_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tc_bg_color.bind("<Key>", lambda e: "break")

        # detached tl
        self.lbl_ex_tl = tk.LabelFrame(self.t4r4, text="• Detached Translated Window Textbox")
        self.lbl_ex_tl.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_ex_tl_max = ttk.Label(self.lbl_ex_tl, text="Max Length")
        self.lbl_ex_tl_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_ex_tl_max, "Maximum length of the textbox. 0 = no limit.")

        self.spn_ex_tl_max = ttk.Spinbox(
            self.lbl_ex_tl,
            from_=0,
            to=10_000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("tb_ex_tl_max", int(self.spn_ex_tl_max.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_ex_tl_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_ex_tl_max, 0, 10_000, lambda: fJson.savePartialSetting("tb_ex_tl_max", int(self.spn_ex_tl_max.get())) or self.preview_changes_tb()))
        self.spn_ex_tl_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.spn_ex_tl_max, "Maximum length of the textbox. 0 = no limit.")

        self.lbl_ex_tl_font = ttk.Label(self.lbl_ex_tl, text="Font")
        self.lbl_ex_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_ex_tl_font = ttk.Combobox(self.lbl_ex_tl, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_ex_tl_font_size = ttk.Label(self.lbl_ex_tl, text="Font Size")
        self.lbl_ex_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spn_ex_tl_font_size = ttk.Spinbox(
            self.lbl_ex_tl,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("tb_ex_tl_font_size", int(self.spn_ex_tl_font_size.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_ex_tl_font_size.bind(
            "<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_ex_tl_font_size, 3, 120, lambda: fJson.savePartialSetting("tb_ex_tl_font_size", int(self.spn_ex_tl_font_size.get())) or self.preview_changes_tb())
        )
        self.spn_ex_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_ex_tl_font_color = ttk.Label(self.lbl_ex_tl, text="Font Color")
        self.lbl_ex_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_tl_font_color = ttk.Entry(self.lbl_ex_tl, width=10)
        self.entry_ex_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_tl_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_font_color, self.entry_ex_tl_font_color.get(), self.root)
            or fJson.savePartialSetting("tb_ex_tl_font_color", self.entry_ex_tl_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tl_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tl_bg_color = ttk.Label(self.lbl_ex_tl, text="Background Color")
        self.lbl_ex_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_tl_bg_color = ttk.Entry(self.lbl_ex_tl, width=10)
        self.entry_ex_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_tl_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_bg_color, self.entry_ex_tl_bg_color.get(), self.root) or fJson.savePartialSetting("tb_ex_tl_bg_color", self.entry_ex_tl_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tl_bg_color.bind("<Key>", lambda e: "break")

        # button
        self.tb_preview_1 = tk.Text(
            self.t4r5,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(fJson.settingCache["tb_mw_tc_font"], fJson.settingCache["tb_mw_tc_font_size"]),
            fg=fJson.settingCache["tb_mw_tc_font_color"],
            bg=fJson.settingCache["tb_mw_tc_bg_color"],
        )
        self.tb_preview_1.bind("<Key>", "break")
        self.tb_preview_1.insert(tk.END, "1234567 Preview プレビュー 预习 предварительный просмотр")
        self.tb_preview_1.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.tb_preview_2 = tk.Text(
            self.t4r5,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(fJson.settingCache["tb_mw_tl_font"], fJson.settingCache["tb_mw_tl_font_size"]),
            fg=fJson.settingCache["tb_mw_tl_font_color"],
            bg=fJson.settingCache["tb_mw_tl_bg_color"],
        )
        self.tb_preview_2.bind("<Key>", "break")
        self.tb_preview_2.insert(tk.END, "1234567 Preview プレビュー 预习 предварительный просмотр")
        self.tb_preview_2.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.tb_preview_3 = tk.Text(
            self.t4r5,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(fJson.settingCache["tb_ex_tc_font"], fJson.settingCache["tb_ex_tc_font_size"]),
            fg=fJson.settingCache["tb_ex_tc_font_color"],
            bg=fJson.settingCache["tb_ex_tc_bg_color"],
        )
        self.tb_preview_3.bind("<Key>", "break")
        self.tb_preview_3.insert(tk.END, "1234567 Preview プレビュー 预习 предварительный просмотр")
        self.tb_preview_3.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.tb_preview_4 = tk.Text(
            self.t4r5,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(fJson.settingCache["tb_ex_tl_font"], fJson.settingCache["tb_ex_tl_font_size"]),
            fg=fJson.settingCache["tb_ex_tl_font_color"],
            bg=fJson.settingCache["tb_ex_tl_bg_color"],
        )
        self.tb_preview_4.bind("<Key>", "break")
        self.tb_preview_4.insert(tk.END, "1234567 Preview プレビュー 预习 предварительный просмотр")
        self.tb_preview_4.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        # ------------------ Tab 5 - Other ------------------
        self.t5r1 = ttk.Frame(self.ft4)
        self.t5r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.lbl_other = tk.LabelFrame(self.t5r1, text="• Application")
        self.lbl_other.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        # check for update on start
        self.check_update_on_start = ttk.Checkbutton(self.lbl_other, text="Check for update on start", command=lambda: fJson.savePartialSetting("checkUpdateOnStart", self.check_update_on_start.instate(["selected"])))
        self.check_update_on_start.pack(side=tk.LEFT, padx=5, pady=5)

        # ------------------ Variables ------------------
        # Flags
        gClass.sw = self  # type: ignore Add self to global class

        # ------------------ Functions ------------------
        self.on_close()  # hide window on start
        self.checkModelOnStart()
        self.deleteLogOnStart()
        self.deleteTempOnStart()
        self.init_setting_once()

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

    def on_close(self):
        self.root.withdraw()

    def on_open(self):
        self.root.geometry(f"950x370")
        self.root.deiconify()

    def init_setting_once(self):
        self.spn_cutOff_mic.set(fJson.settingCache["cutOff_mic"])
        self.spn_cutOff_speaker.set(fJson.settingCache["cutOff_speaker"])
        self.spn_max_temp.set(fJson.settingCache["max_temp"])

        self.entry_separate_text_with.delete(0, tk.END)
        self.entry_separate_text_with.insert(0, fJson.settingCache["separate_with"])

        self.entry_libre_key.delete(0, tk.END)
        self.entry_libre_key.insert(0, fJson.settingCache["libre_api_key"])
        self.entry_libre_host.delete(0, tk.END)
        self.entry_libre_host.insert(0, fJson.settingCache["libre_host"])
        self.entry_libre_port.delete(0, tk.END)
        self.entry_libre_port.insert(0, fJson.settingCache["libre_port"])

        self.init_tb_settings(fJson.settingCache)

        if platform.system() == "Windows":
            if fJson.settingCache["hide_console_window_on_start"]:
                self.cbtn_hide_console_window_on_start.invoke()
            else:
                self.cbtn_hide_console_window_on_start.invoke()
                self.cbtn_hide_console_window_on_start.invoke()

        if fJson.settingCache["keep_audio"]:
            self.cbtn_keep_audio.invoke()
        else:
            self.cbtn_keep_audio.invoke()
            self.cbtn_keep_audio.invoke()

        if fJson.settingCache["keep_log"]:
            self.cbtn_keep_log.invoke()
        else:
            self.cbtn_keep_log.invoke()
            self.cbtn_keep_log.invoke()

        if fJson.settingCache["verbose"]:
            self.cbtn_verbose.invoke()
        else:
            self.cbtn_verbose.invoke()
            self.cbtn_verbose.invoke()

        if fJson.settingCache["checkUpdateOnStart"]:
            self.check_update_on_start.invoke()
        else:
            self.check_update_on_start.invoke()
            self.check_update_on_start.invoke()

        if fJson.settingCache["libre_https"]:
            self.cbtn_libre_https.invoke()
        else:
            self.cbtn_libre_https.invoke()
            self.cbtn_libre_https.invoke()

    def tb_delete(self):
        self.entry_mw_tc_font_color.delete(0, tk.END)
        self.entry_mw_tc_bg_color.delete(0, tk.END)

        self.entry_mw_tl_font_color.delete(0, tk.END)
        self.entry_mw_tl_bg_color.delete(0, tk.END)

        self.entry_ex_tc_font_color.delete(0, tk.END)
        self.entry_ex_tc_bg_color.delete(0, tk.END)

        self.entry_ex_tl_font_color.delete(0, tk.END)
        self.entry_ex_tl_bg_color.delete(0, tk.END)

    def init_tb_settings(self, theSetting):
        self.tb_delete()
        self.spn_mw_tc_max.set(theSetting["tb_mw_tc_max"])
        self.cb_mw_tc_font.set(theSetting["tb_mw_tc_font"])
        self.spn_mw_tc_font_size.set(theSetting["tb_mw_tc_font_size"])
        self.entry_mw_tc_font_color.insert(0, theSetting["tb_mw_tc_font_color"])
        self.entry_mw_tc_bg_color.insert(0, theSetting["tb_mw_tc_bg_color"])

        self.spn_mw_tl_max.set(theSetting["tb_mw_tl_max"])
        self.cb_mw_tl_font.set(theSetting["tb_mw_tl_font"])
        self.spn_mw_tl_font_size.set(theSetting["tb_mw_tl_font_size"])
        self.entry_mw_tl_font_color.insert(0, theSetting["tb_mw_tl_font_color"])
        self.entry_mw_tl_bg_color.insert(0, theSetting["tb_mw_tl_bg_color"])

        self.spn_ex_tc_max.set(theSetting["tb_ex_tc_max"])
        self.cb_ex_tc_font.set(theSetting["tb_ex_tc_font"])
        self.spn_ex_tc_font_size.set(theSetting["tb_ex_tc_font_size"])
        self.entry_ex_tc_font_color.insert(0, theSetting["tb_ex_tc_font_color"])
        self.entry_ex_tc_bg_color.insert(0, theSetting["tb_ex_tc_bg_color"])

        self.spn_ex_tl_max.set(theSetting["tb_ex_tl_max"])
        self.cb_ex_tl_font.set(theSetting["tb_ex_tl_font"])
        self.spn_ex_tl_font_size.set(theSetting["tb_ex_tl_font_size"])
        self.entry_ex_tl_font_color.insert(0, theSetting["tb_ex_tl_font_color"])
        self.entry_ex_tl_bg_color.insert(0, theSetting["tb_ex_tl_bg_color"])

    def preview_changes_tb(self):
        assert gClass.mw is not None
        gClass.mw.tb_transcribed.config(
            font=(self.cb_mw_tc_font.get(), int(self.spn_mw_tc_font_size.get())),
            fg=self.entry_mw_tc_font_color.get(),
            bg=self.entry_mw_tc_bg_color.get(),
        )
        self.tb_preview_1.config(
            font=(self.cb_mw_tc_font.get(), int(self.spn_mw_tc_font_size.get())),
            fg=self.entry_mw_tc_font_color.get(),
            bg=self.entry_mw_tc_bg_color.get(),
        )

        gClass.mw.tb_translated.config(
            font=(self.cb_mw_tl_font.get(), int(self.spn_mw_tl_font_size.get())),
            fg=self.entry_mw_tl_font_color.get(),
            bg=self.entry_mw_tl_bg_color.get(),
        )
        self.tb_preview_2.config(
            font=(self.cb_mw_tl_font.get(), int(self.spn_mw_tl_font_size.get())),
            fg=self.entry_mw_tl_font_color.get(),
            bg=self.entry_mw_tl_bg_color.get(),
        )

        assert gClass.ex_tcw is not None
        gClass.ex_tcw.textbox.config(
            font=(self.cb_ex_tc_font.get(), int(self.spn_ex_tc_font_size.get())),
            fg=self.entry_ex_tc_font_color.get(),
            bg=self.entry_ex_tc_bg_color.get(),
        )
        self.tb_preview_3.config(
            font=(self.cb_ex_tc_font.get(), int(self.spn_ex_tc_font_size.get())),
            fg=self.entry_ex_tc_font_color.get(),
            bg=self.entry_ex_tc_bg_color.get(),
        )

        assert gClass.ex_tlw is not None
        gClass.ex_tlw.textbox.config(
            font=(self.cb_ex_tl_font.get(), int(self.spn_ex_tl_font_size.get())),
            fg=self.entry_ex_tl_font_color.get(),
            bg=self.entry_ex_tl_bg_color.get(),
        )
        self.tb_preview_4.config(
            font=(self.cb_ex_tl_font.get(), int(self.spn_ex_tl_font_size.get())),
            fg=self.entry_ex_tl_font_color.get(),
            bg=self.entry_ex_tl_bg_color.get(),
        )

    def number_only(self, P):
        return P.isdigit()

    def verifyMaxNumber(self, el, min: int, max: int, cb_func=None):
        value = el.get()

        if int(value) > max:
            el.set(max)

        if int(value) < min:
            el.set(min)

        if cb_func is not None:
            cb_func()

    def deleteTheLog(self):
        # delete all log files
        for file in os.listdir(dir_log):
            if file.endswith(".log"):
                try:
                    os.remove(os.path.join(dir_log, file))
                except Exception as e:
                    if file != current_log:  # show warning only if the fail to delete is not the current log
                        logger.warning("Failed to delete log file: " + file)
                        logger.warning("Reason " + str(e))
                    pass

    def deleteTemp(self):
        # delete all temp wav files
        for file in os.listdir(dir_temp):
            if file.endswith(".wav"):
                try:
                    os.remove(os.path.join(dir_temp, file))
                except Exception as e:
                    logger.warning("Failed to delete temp file: " + file)
                    logger.warning("Reason " + str(e))
                    pass

    def deleteLogOnStart(self):
        if not fJson.settingCache["keep_log"]:
            self.deleteTheLog()

    def deleteTempOnStart(self):
        if not fJson.settingCache["keep_audio"]:
            self.deleteTemp()

    def promptDeleteLog(self):
        # confirmation using mbox
        if Mbox("Delete Log Files", "Are you sure you want to delete all log files?", 3, self.root):
            # delete all log files
            self.deleteTheLog()

            # confirmation using mbox
            Mbox("Delete Log Files", "Log files deleted successfully!", 0, self.root)

    def model_check(self, model: str, btn: ttk.Button) -> None:
        downloaded = verify_model(model)

        if not downloaded:
            Mbox("Model not found", "Model not found or checksum does not match. You can press download to download the model.", 0, self.root)
            btn.config(text="Download", command=lambda: self.modelDownload(model, btn))
        else:
            btn.config(text="Downloaded", state=tk.DISABLED)

    def modelDownload(self, model: str, btn: ttk.Button) -> None:
        # if already downloading then return
        if gClass.dl_proc is not None:
            Mbox("Already downloading", "Please wait for the current download to finish.", 0, self.root)
            return

        # Download model
        gClass.dl_proc = Process(target=download_model, args=(model,), daemon=True)
        gClass.dl_proc.start()

        # Update button
        btn.config(text="Downloading... (Click to cancel)", command=lambda: self.modelDownloadCancel(model, btn))

        # notify
        Mbox("Downloading model...", "Check the log for more information", 0, self.root)

    def modelDownloadCancel(self, model: str, btn: ttk.Button) -> None:
        # Kill process
        if gClass.dl_proc is not None:
            gClass.dl_proc.terminate()
            gClass.dl_proc = None

        # Update button
        btn.config(text="Download", command=lambda: self.modelDownload(model, btn))

        # notify
        Mbox("Download cancelled.", "Model download cancelled.", 0, self.root)

    def checkModelOnStart(self):
        """
        Check if model is downloaded on start.
        It need to be checked hardcodedly because for some reason if i try to use a map it keep referencing to the wrong button.
        """
        checkTiny = verify_model("tiny")
        checkTinyEn = verify_model("tiny.en")
        checkBase = verify_model("base")
        checkBaseEn = verify_model("base.en")
        checkSmall = verify_model("small")
        checkSmallEn = verify_model("small.en")
        checkMedium = verify_model("medium")
        checkMediumEn = verify_model("medium.en")
        checkLarge = verify_model("large")

        if not checkTiny:
            self.btn_interact_tiny.config(text="Download", command=lambda: self.modelDownload("tiny", self.btn_interact_tiny))
        else:
            self.btn_interact_tiny.config(text="Downloaded", state=tk.DISABLED)

        if not checkTinyEn:
            self.btn_interact_tiny_eng.config(text="Download", command=lambda: self.modelDownload("tiny.en", self.btn_interact_tiny_eng))
        else:
            self.btn_interact_tiny_eng.config(text="Downloaded", state=tk.DISABLED)

        if not checkBase:
            self.btn_interact_base.config(text="Download", command=lambda: self.modelDownload("base", self.btn_interact_base))
        else:
            self.btn_interact_base.config(text="Downloaded", state=tk.DISABLED)

        if not checkBaseEn:
            self.btn_interact_base_eng.config(text="Download", command=lambda: self.modelDownload("base.en", self.btn_interact_base_eng))
        else:
            self.btn_interact_base_eng.config(text="Downloaded", state=tk.DISABLED)

        if not checkSmall:
            self.btn_interact_small.config(text="Download", command=lambda: self.modelDownload("small", self.btn_interact_small))
        else:
            self.btn_interact_small.config(text="Downloaded", state=tk.DISABLED)

        if not checkSmallEn:
            self.btn_interact_small_eng.config(text="Download", command=lambda: self.modelDownload("small.en", self.btn_interact_small_eng))
        else:
            self.btn_interact_small_eng.config(text="Downloaded", state=tk.DISABLED)

        if not checkMedium:
            self.btn_interact_medium.config(text="Download", command=lambda: self.modelDownload("medium", self.btn_interact_medium))
        else:
            self.btn_interact_medium.config(text="Downloaded", state=tk.DISABLED)

        if not checkMediumEn:
            self.btn_interact_medium_eng.config(text="Download", command=lambda: self.modelDownload("medium.en", self.btn_interact_medium_eng))
        else:
            self.btn_interact_medium_eng.config(text="Downloaded", state=tk.DISABLED)

        if not checkLarge:
            self.btn_interact_large.config(text="Download", command=lambda: self.modelDownload("large", self.btn_interact_large))
        else:
            self.btn_interact_large.config(text="Downloaded", state=tk.DISABLED)
