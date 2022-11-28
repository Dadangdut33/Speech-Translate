import os
import platform
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font, colorchooser
from multiprocessing import Process

# User defined
from speech_translate.Globals import app_icon, app_name, fJson, gClass, dir_log
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
        self.root.geometry("1080x370")
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

        self.frame_tab1 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.frame_tab1, text="General")

        self.frame_tab2 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.frame_tab2, text="Translation")

        self.frame_tab3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.frame_tab3, text="Textbox")

        self.frame_tab4 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.frame_tab4, text="Other")

        # ------------------ Widgets - General ------------------
        self.lf_t1r1 = ttk.LabelFrame(self.frame_tab1, text="• Audio Capture")
        self.lf_t1r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # cutoff
        # 1
        self.t1r1_1 = ttk.Frame(self.lf_t1r1)
        self.t1r1_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.label_cutOff_mic = ttk.Label(self.t1r1_1, text="Mic Cutoff: ")
        self.label_cutOff_mic.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_cutOff_mic, "Set the cut off length (in seconds) for microphone input.")

        self.spinner_cutOff_mic = ttk.Spinbox(
            self.t1r1_1,
            from_=3,
            to=30,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("cutOff", {"mic": int(self.spinner_cutOff_mic.get()), "speaker": int(self.spinner_cutOff_speaker.get())}),
        )
        self.spinner_cutOff_mic.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(self.spinner_cutOff_mic, 3, 30, lambda: fJson.savePartialSetting("cutOff", {"mic": int(self.spinner_cutOff_mic.get()), "speaker": int(self.spinner_cutOff_speaker.get())})),
        )
        self.spinner_cutOff_mic.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spinner_cutOff_mic, "Set the cut off length (in seconds) for microphone input.")

        self.label_cutOff_speaker = ttk.Label(self.t1r1_1, text="Speaker Cutoff: ")
        self.label_cutOff_speaker.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_cutOff_speaker, "Set the cut off length (in seconds) for speaker input.")

        self.spinner_cutOff_speaker = ttk.Spinbox(
            self.t1r1_1,
            from_=3,
            to=30,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("cutOff", {"mic": int(self.spinner_cutOff_mic.get()), "speaker": int(self.spinner_cutOff_speaker.get())}),
        )
        self.spinner_cutOff_speaker.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(self.spinner_cutOff_speaker, 3, 30, lambda: fJson.savePartialSetting("cutOff", {"mic": int(self.spinner_cutOff_mic.get()), "speaker": int(self.spinner_cutOff_speaker.get())})),
        )
        self.spinner_cutOff_speaker.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spinner_cutOff_speaker, "Set the cut off length (in seconds) for speaker input.")

        # 2
        self.t1r1_2 = ttk.Frame(self.lf_t1r1)
        self.t1r1_2.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.label_separate_text_with = ttk.Label(self.t1r1_2, text="Text Separator: ")
        self.label_separate_text_with.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_separate_text_with, "Set the separator for text that is transcribed/translated.\n\n. Default value \\n", wrapLength=400)

        self.entry_separate_text_with = ttk.Entry(self.t1r1_2)
        self.entry_separate_text_with.pack(side=tk.LEFT, padx=5)
        self.entry_separate_text_with.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("separate_with", self.entry_separate_text_with.get()))
        CreateToolTip(self.entry_separate_text_with, "Set the separator for text that is transcribed/translated.\n\nDefault value \\n", wrapLength=400)

        # 3
        self.t1r1_3 = ttk.Frame(self.lf_t1r1)
        self.t1r1_3.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.label_max_temp = ttk.Label(self.t1r1_3, text="Max Temp File: ")
        self.label_max_temp.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_max_temp, "Set max number of audio temp files before deletion in each recording session")

        self.spinner_max_temp = ttk.Spinbox(
            self.t1r1_3, from_=10, to=500, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: fJson.savePartialSetting("max_temp", int(self.spinner_max_temp.get()))
        )
        self.spinner_max_temp.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spinner_max_temp, 10, 500, lambda: fJson.savePartialSetting("max_temp", int(self.spinner_max_temp.get()))))
        self.spinner_max_temp.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spinner_max_temp, "Set max number of audio temp files before deletion in each recording session")

        self.checkbutton_keep_audio = ttk.Checkbutton(self.t1r1_3, text="Keep Audio", command=lambda: fJson.savePartialSetting("keep_audio", self.checkbutton_keep_audio.instate(["selected"])))
        self.checkbutton_keep_audio.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.checkbutton_keep_audio, "Keep audio files after transcription/translation")

        # log
        self.lf_t1r2 = ttk.LabelFrame(self.frame_tab1, text="• Logging")
        self.lf_t1r2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t1_r2_1 = ttk.Frame(self.lf_t1r2)
        self.t1_r2_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.label_log_location = ttk.Label(self.t1_r2_1, text="Log Files Location: ")
        self.label_log_location.pack(side=tk.LEFT, padx=5)

        self.label_log_location_value = ttk.Label(self.t1_r2_1, text=dir_log, cursor="hand2")
        self.label_log_location_value.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_log_location_value, "Location of log file.\n- LClick to open the folder.\n-RClick to delete all log files.")
        self.label_log_location_value.bind("<Button-1>", lambda e: startFile(dir_log))
        self.label_log_location_value.bind("<Button-3>", lambda e: self.promptDeleteLog())

        self.t1_r2_2 = ttk.Frame(self.lf_t1r2)
        self.t1_r2_2.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.checkbutton_keep_log = ttk.Checkbutton(self.t1_r2_2, text="Keep Log Files", command=lambda: fJson.savePartialSetting("keep_log", self.checkbutton_keep_log.instate(["selected"])))
        self.checkbutton_keep_log.pack(side=tk.LEFT, padx=5, pady=5)

        self.checkbutton_verbose = ttk.Checkbutton(self.t1_r2_2, text="Verbose Logging for Whisper", command=lambda: fJson.savePartialSetting("verbose", self.checkbutton_verbose.instate(["selected"])))
        self.checkbutton_verbose.pack(side=tk.LEFT, padx=5)

        # only on windows
        if platform.system() == "Windows":
            self.checkbutton_hide_console_window_on_start = ttk.Checkbutton(
                self.t1_r2_2, text="Hide Console Window on Start", command=lambda: fJson.savePartialSetting("hide_console_window_on_start", self.checkbutton_hide_console_window_on_start.instate(["selected"]))
            )
            self.checkbutton_hide_console_window_on_start.pack(side=tk.LEFT, padx=5)
            CreateToolTip(self.checkbutton_hide_console_window_on_start, "Will hide console (log) window every program start. Only on Windows.")

        # model
        self.lf_t1r3 = ttk.LabelFrame(self.frame_tab1, text="• Model")
        self.lf_t1r3.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # label model location
        self.t1_r3_1 = ttk.Frame(self.lf_t1r3)
        self.t1_r3_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.label_model_location = ttk.Label(self.t1_r3_1, text="Model Location: ")
        self.label_model_location.pack(side=tk.LEFT, padx=5)

        self.label_model_location_value = ttk.Label(self.t1_r3_1, text="None", cursor="hand2")
        self.label_model_location_value.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_model_location_value, "Location of the model file.\nLClick to open the folder")
        self.label_model_location_value.bind("<Button-1>", lambda e: startFile(self.label_model_location_value.cget("text")))

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
        self.lf_t3r1 = ttk.LabelFrame(self.frame_tab2, text="• Libre Translate Setting")
        self.lf_t3r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.label_libre_key = ttk.Label(self.lf_t3r1, text="Libre Translate API Key")
        self.label_libre_key.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.label_libre_key, "Libre Translate API Key. Leave empty if not needed or host locally.")

        self.entry_libre_key = ttk.Entry(self.lf_t3r1)
        self.entry_libre_key.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_libre_key.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_api_key", self.entry_libre_key.get()))

        self.label_libre_host = ttk.Label(self.lf_t3r1, text="Libre Translate Host")
        self.label_libre_host.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_libre_host = ttk.Entry(self.lf_t3r1)
        self.entry_libre_host.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_libre_host.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_host", self.entry_libre_host.get()))

        self.label_libre_port = ttk.Label(self.lf_t3r1, text="Libre Translate Port")
        self.label_libre_port.pack(side=tk.LEFT, padx=5, pady=5)
        self.label_libre_port.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_port", self.entry_libre_port.get()))

        self.entry_libre_port = ttk.Entry(self.lf_t3r1)
        self.entry_libre_port.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_libre_port.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_port", self.entry_libre_port.get()))

        self.checkbutton_libre_https = ttk.Checkbutton(self.lf_t3r1, text="Use HTTPS", command=lambda: fJson.savePartialSetting("libre_https", self.checkbutton_libre_https.instate(["selected"])))
        self.checkbutton_libre_https.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkbutton_libre_https, "Don't use this if you're hosting locally.")

        # ------------------ Widgets - Textbox ------------------
        self.t4r1 = ttk.Frame(self.frame_tab3)
        self.t4r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t4r2 = ttk.Frame(self.frame_tab3)
        self.t4r2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t4r3 = ttk.Frame(self.frame_tab3)
        self.t4r3.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t4r4 = ttk.Frame(self.frame_tab3)
        self.t4r4.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t4r5 = ttk.Frame(self.frame_tab3)
        self.t4r5.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # mw tc
        self.label_mw_tc = ttk.LabelFrame(self.t4r1, text="• Main Window Transcribed Textbox")
        self.label_mw_tc.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tc_max = ttk.Label(self.label_mw_tc, text="Max Length")
        self.label_mw_tc_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.spinner_mw_tc_max = ttk.Spinbox(self.label_mw_tc, from_=50, to=10_000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinner_mw_tc_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spinner_mw_tc_max, 50, 10_000))
        self.spinner_mw_tc_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tc_font = ttk.Label(self.label_mw_tc, text="Font")
        self.label_mw_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.select_mw_tc_font = ttk.Combobox(self.label_mw_tc, values=self.fonts, state="readonly")
        self.select_mw_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tc_font_size = ttk.Label(self.label_mw_tc, text="Font Size")
        self.label_mw_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spinbox_mw_tc_font_size = ttk.Spinbox(self.label_mw_tc, from_=3, to=120, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinbox_mw_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tc_font_color = ttk.Label(self.label_mw_tc, text="Font Color")
        self.label_mw_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_font_color = ttk.Entry(self.label_mw_tc)
        self.entry_mw_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tc_font_color.bind("<Button-1>", lambda e: chooseColor(self.entry_mw_tc_font_color, self.entry_mw_tc_font_color.get(), self.root))
        self.entry_mw_tc_font_color.bind("<Key>", lambda e: "break")

        self.label_mw_tc_bg_color = ttk.Label(self.label_mw_tc, text="Background Color")
        self.label_mw_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_bg_color = ttk.Entry(self.label_mw_tc)
        self.entry_mw_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tc_bg_color.bind("<Button-1>", lambda e: chooseColor(self.entry_mw_tc_bg_color, self.entry_mw_tc_bg_color.get(), self.root))
        self.entry_mw_tc_bg_color.bind("<Key>", lambda e: "break")

        # mw tl
        self.label_mw_tl = ttk.LabelFrame(self.t4r2, text="• Main Window Translated Textbox")
        self.label_mw_tl.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tl_max = ttk.Label(self.label_mw_tl, text="Max Length")
        self.label_mw_tl_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.spinner_mw_tl_max = ttk.Spinbox(self.label_mw_tl, from_=50, to=10_000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinner_mw_tl_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spinner_mw_tl_max, 50, 10_000))
        self.spinner_mw_tl_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tl_font = ttk.Label(self.label_mw_tl, text="Font")
        self.label_mw_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.select_mw_tl_font = ttk.Combobox(self.label_mw_tl, values=self.fonts, state="readonly")
        self.select_mw_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tl_font_size = ttk.Label(self.label_mw_tl, text="Font Size")
        self.label_mw_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spinbox_mw_tl_font_size = ttk.Spinbox(self.label_mw_tl, from_=3, to=120, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinbox_mw_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tl_font_color = ttk.Label(self.label_mw_tl, text="Font Color")
        self.label_mw_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_font_color = ttk.Entry(self.label_mw_tl)
        self.entry_mw_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tl_font_color.bind("<Button-1>", lambda e: chooseColor(self.entry_mw_tl_font_color, self.entry_mw_tl_font_color.get(), self.root))
        self.entry_mw_tl_font_color.bind("<Key>", lambda e: "break")

        self.label_mw_tl_bg_color = ttk.Label(self.label_mw_tl, text="Background Color")
        self.label_mw_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_bg_color = ttk.Entry(self.label_mw_tl)
        self.entry_mw_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tl_bg_color.bind("<Button-1>", lambda e: chooseColor(self.entry_mw_tl_bg_color, self.entry_mw_tl_bg_color.get(), self.root))
        self.entry_mw_tl_bg_color.bind("<Key>", lambda e: "break")

        # detached tc
        self.label_detached_tc = ttk.LabelFrame(self.t4r3, text="• Detached Transcribed Window Textbox")
        self.label_detached_tc.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tc_max = ttk.Label(self.label_detached_tc, text="Max Length")
        self.label_detached_tc_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.spinner_detached_tc_max = ttk.Spinbox(self.label_detached_tc, from_=50, to=10_000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinner_detached_tc_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spinner_detached_tc_max, 50, 10_000))
        self.spinner_detached_tc_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tc_font = ttk.Label(self.label_detached_tc, text="Font")
        self.label_detached_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.select_detached_tc_font = ttk.Combobox(self.label_detached_tc, values=self.fonts, state="readonly")
        self.select_detached_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tc_font_size = ttk.Label(self.label_detached_tc, text="Font Size")
        self.label_detached_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spinbox_detached_tc_font_size = ttk.Spinbox(self.label_detached_tc, from_=3, to=120, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinbox_detached_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tc_font_color = ttk.Label(self.label_detached_tc, text="Font Color")
        self.label_detached_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tc_font_color = ttk.Entry(self.label_detached_tc)
        self.entry_detached_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_detached_tc_font_color.bind("<Button-1>", lambda e: chooseColor(self.entry_detached_tc_font_color, self.entry_detached_tc_font_color.get(), self.root))
        self.entry_detached_tc_font_color.bind("<Key>", lambda e: "break")

        self.label_detached_tc_bg_color = ttk.Label(self.label_detached_tc, text="Background Color")
        self.label_detached_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tc_bg_color = ttk.Entry(self.label_detached_tc)
        self.entry_detached_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_detached_tc_bg_color.bind("<Button-1>", lambda e: chooseColor(self.entry_detached_tc_bg_color, self.entry_detached_tc_bg_color.get(), self.root))
        self.entry_detached_tc_bg_color.bind("<Key>", lambda e: "break")

        # detached tl
        self.label_detached_tl = ttk.LabelFrame(self.t4r4, text="• Detached Translated Window Textbox")
        self.label_detached_tl.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tl_max = ttk.Label(self.label_detached_tl, text="Max Length")
        self.label_detached_tl_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.spinner_detached_tl_max = ttk.Spinbox(self.label_detached_tl, from_=50, to=10_000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinner_detached_tl_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spinner_detached_tl_max, 50, 10_000))
        self.spinner_detached_tl_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tl_font = ttk.Label(self.label_detached_tl, text="Font")
        self.label_detached_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.select_detached_tl_font = ttk.Combobox(self.label_detached_tl, values=self.fonts, state="readonly")
        self.select_detached_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tl_font_size = ttk.Label(self.label_detached_tl, text="Font Size")
        self.label_detached_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spinbox_detached_tl_font_size = ttk.Spinbox(self.label_detached_tl, from_=3, to=120, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinbox_detached_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tl_font_color = ttk.Label(self.label_detached_tl, text="Font Color")
        self.label_detached_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tl_font_color = ttk.Entry(self.label_detached_tl)
        self.entry_detached_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_detached_tl_font_color.bind("<Button-1>", lambda e: chooseColor(self.entry_detached_tl_font_color, self.entry_detached_tl_font_color.get(), self.root))
        self.entry_detached_tl_font_color.bind("<Key>", lambda e: "break")

        self.label_detached_tl_bg_color = ttk.Label(self.label_detached_tl, text="Background Color")
        self.label_detached_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tl_bg_color = ttk.Entry(self.label_detached_tl)
        self.entry_detached_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_detached_tl_bg_color.bind("<Button-1>", lambda e: chooseColor(self.entry_detached_tl_bg_color, self.entry_detached_tl_bg_color.get(), self.root))
        self.entry_detached_tl_bg_color.bind("<Key>", lambda e: "break")

        # button
        self.btn_reset_default = ttk.Button(self.t4r5, text="Reset to Default", command=self.reset_textbox_setting)
        self.btn_reset_default.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.btn_reset_default, "Reset all textbox setting to default value")

        self.btn_cancel = ttk.Button(self.t4r5, text="Cancel", command=lambda: self.cancel_tb(True))
        self.btn_cancel.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.btn_cancel, "Cancecl changes made to the textbox settings")

        self.btn_save = ttk.Button(self.t4r5, text="Save", command=self.save_tb)
        self.btn_save.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.btn_save, "Save changes made to the textbox settings for future use")

        self.btn_preview_changes = ttk.Button(self.t4r5, text="Preview Changes", command=self.preview_changes_tb)
        self.btn_preview_changes.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.btn_preview_changes, "Preview changes made to the textbox settings. If not saved will revert to previous setting on next launch")

        # ------------------ Tab 5 - Other ------------------
        self.t5r1 = ttk.Frame(self.frame_tab4)
        self.t5r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.label_other = ttk.LabelFrame(self.t5r1, text="• Application")
        self.label_other.pack(side=tk.LEFT, padx=5, pady=5)

        # check for update on start
        self.check_update_on_start = ttk.Checkbutton(self.label_other, text="Check for update on start", command=lambda: fJson.savePartialSetting("checkUpdateOnStart", self.check_update_on_start.instate(["selected"])))
        self.check_update_on_start.pack(side=tk.LEFT, padx=5, pady=5)

        # ------------------ Variables ------------------
        # Flags
        gClass.sw = self  # type: ignore Add self to global class

        # ------------------ Functions ------------------
        self.on_close()  # hide window on start
        self.checkModelOnStart()
        self.deleteLogOnStart()
        self.init_setting_once()

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

    def on_close(self):
        self.root.withdraw()

    def on_open(self):
        self.root.deiconify()

    def init_setting_once(self):
        self.spinner_cutOff_mic.set(fJson.settingCache["cutOff"]["mic"])
        self.spinner_cutOff_speaker.set(fJson.settingCache["cutOff"]["speaker"])
        self.spinner_max_temp.set(fJson.settingCache["max_temp"])

        self.entry_separate_text_with.delete(0, tk.END)
        self.entry_separate_text_with.insert(0, fJson.settingCache["separate_with"])

        self.entry_libre_key.delete(0, tk.END)
        self.entry_libre_key.insert(0, fJson.settingCache["libre_api_key"])
        self.entry_libre_host.delete(0, tk.END)
        self.entry_libre_host.insert(0, fJson.settingCache["libre_host"])
        self.entry_libre_port.delete(0, tk.END)
        self.entry_libre_port.insert(0, fJson.settingCache["libre_port"])

        self.reset_tb_helper(fJson.settingCache)

        if platform.system() == "Windows":
            if fJson.settingCache["hide_console_window_on_start"]:
                self.checkbutton_hide_console_window_on_start.invoke()
            else:
                self.checkbutton_hide_console_window_on_start.invoke()
                self.checkbutton_hide_console_window_on_start.invoke()

        if fJson.settingCache["keep_audio"]:
            self.checkbutton_keep_audio.invoke()
        else:
            self.checkbutton_keep_audio.invoke()
            self.checkbutton_keep_audio.invoke()

        if fJson.settingCache["keep_log"]:
            self.checkbutton_keep_log.invoke()
        else:
            self.checkbutton_keep_log.invoke()
            self.checkbutton_keep_log.invoke()

        if fJson.settingCache["verbose"]:
            self.checkbutton_verbose.invoke()
        else:
            self.checkbutton_verbose.invoke()
            self.checkbutton_verbose.invoke()

        if fJson.settingCache["checkUpdateOnStart"]:
            self.check_update_on_start.invoke()
        else:
            self.check_update_on_start.invoke()
            self.check_update_on_start.invoke()

        if fJson.settingCache["libre_https"]:
            self.checkbutton_libre_https.invoke()
        else:
            self.checkbutton_libre_https.invoke()
            self.checkbutton_libre_https.invoke()

    def cancel_tb(self, withConfirmation=False):
        if withConfirmation:
            if not Mbox("Cancel Changes", "Are you sure you want to cancel any changes made?", 3, self.root):
                return

        self.reset_tb_helper(fJson.settingCache)
        self.preview_changes_tb()

    def reset_textbox_setting(self):
        if not Mbox("Reset Default Textbox Settings", "Are you sure you want to reset the textbox settings to default?", 3, self.root):
            return

        self.reset_tb_helper(default_setting)

    def tb_delete(self):
        self.entry_mw_tc_font_color.delete(0, tk.END)
        self.entry_mw_tc_bg_color.delete(0, tk.END)

        self.entry_mw_tl_font_color.delete(0, tk.END)
        self.entry_mw_tl_bg_color.delete(0, tk.END)

        self.entry_detached_tc_font_color.delete(0, tk.END)
        self.entry_detached_tc_bg_color.delete(0, tk.END)

        self.entry_detached_tl_font_color.delete(0, tk.END)
        self.entry_detached_tl_bg_color.delete(0, tk.END)

    def reset_tb_helper(self, theSetting):
        self.tb_delete()
        self.spinner_mw_tc_max.set(theSetting["textbox"]["mw_tc"]["max"])
        self.select_mw_tc_font.set(theSetting["textbox"]["mw_tc"]["font"])
        self.spinbox_mw_tc_font_size.set(theSetting["textbox"]["mw_tc"]["font_size"])
        self.entry_mw_tc_font_color.insert(0, theSetting["textbox"]["mw_tc"]["font_color"])
        self.entry_mw_tc_bg_color.insert(0, theSetting["textbox"]["mw_tc"]["bg_color"])

        self.spinner_mw_tl_max.set(theSetting["textbox"]["mw_tl"]["max"])
        self.select_mw_tl_font.set(theSetting["textbox"]["mw_tl"]["font"])
        self.spinbox_mw_tl_font_size.set(theSetting["textbox"]["mw_tl"]["font_size"])
        self.entry_mw_tl_font_color.insert(0, theSetting["textbox"]["mw_tl"]["font_color"])
        self.entry_mw_tl_bg_color.insert(0, theSetting["textbox"]["mw_tl"]["bg_color"])

        self.spinner_detached_tc_max.set(theSetting["textbox"]["detached_tc"]["max"])
        self.select_detached_tc_font.set(theSetting["textbox"]["detached_tc"]["font"])
        self.spinbox_detached_tc_font_size.set(theSetting["textbox"]["detached_tc"]["font_size"])
        self.entry_detached_tc_font_color.insert(0, theSetting["textbox"]["detached_tc"]["font_color"])
        self.entry_detached_tc_bg_color.insert(0, theSetting["textbox"]["detached_tc"]["bg_color"])

        self.spinner_detached_tl_max.set(theSetting["textbox"]["detached_tl"]["max"])
        self.select_detached_tl_font.set(theSetting["textbox"]["detached_tl"]["font"])
        self.spinbox_detached_tl_font_size.set(theSetting["textbox"]["detached_tl"]["font_size"])
        self.entry_detached_tl_font_color.insert(0, theSetting["textbox"]["detached_tl"]["font_color"])
        self.entry_detached_tl_bg_color.insert(0, theSetting["textbox"]["detached_tl"]["bg_color"])

    def save_tb(self):
        # confirmation
        if not Mbox("Save", "Are you sure you want to save the changes made for the textbox setting?", 3, self.root):
            return

        saveVal = {
            "mw_tc": {
                "max": int(self.spinner_mw_tc_max.get()),
                "font": self.select_mw_tc_font.get(),
                "font_size": int(self.spinbox_mw_tc_font_size.get()),
                "font_color": self.entry_mw_tc_font_color.get(),
                "bg_color": self.entry_mw_tc_bg_color.get(),
            },
            "mw_tl": {
                "max": int(self.spinner_mw_tl_max.get()),
                "font": self.select_mw_tl_font.get(),
                "font_size": int(self.spinbox_mw_tl_font_size.get()),
                "font_color": self.entry_mw_tl_font_color.get(),
                "bg_color": self.entry_mw_tl_bg_color.get(),
            },
            "detached_tc": {
                "max": int(self.spinner_detached_tc_max.get()),
                "font": self.select_detached_tc_font.get(),
                "font_size": int(self.spinbox_detached_tc_font_size.get()),
                "font_color": self.entry_detached_tc_font_color.get(),
                "bg_color": self.entry_detached_tc_bg_color.get(),
            },
            "detached_tl": {
                "max": int(self.spinner_detached_tl_max.get()),
                "font": self.select_detached_tl_font.get(),
                "font_size": int(self.spinbox_detached_tl_font_size.get()),
                "font_color": self.entry_detached_tl_font_color.get(),
                "bg_color": self.entry_detached_tl_bg_color.get(),
            },
        }

        fJson.savePartialSetting("textbox", saveVal)

        # notify
        Mbox("Textbox setting saved", "The textbox setting has been saved successfully.", 0, self.root)

    def preview_changes_tb(self):
        assert gClass.detached_tcw is not None
        gClass.detached_tcw.textbox.config(
            font=(self.select_detached_tc_font.get(), int(self.spinbox_detached_tc_font_size.get())),
            fg=self.entry_detached_tc_font_color.get(),
            bg=self.entry_detached_tc_bg_color.get(),
        )

        assert gClass.detached_tlw is not None
        gClass.detached_tlw.textbox.config(
            font=(self.select_detached_tl_font.get(), int(self.spinbox_detached_tl_font_size.get())),
            fg=self.entry_detached_tl_font_color.get(),
            bg=self.entry_detached_tl_bg_color.get(),
        )

        assert gClass.mw is not None
        gClass.mw.tb_transcribed.config(
            font=(self.select_mw_tc_font.get(), int(self.spinbox_mw_tc_font_size.get())),
            fg=self.entry_mw_tc_font_color.get(),
            bg=self.entry_mw_tc_bg_color.get(),
        )

        gClass.mw.tb_translated.config(
            font=(self.select_mw_tl_font.get(), int(self.spinbox_mw_tl_font_size.get())),
            fg=self.entry_mw_tl_font_color.get(),
            bg=self.entry_mw_tl_bg_color.get(),
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

    def deleteLogOnStart(self):
        if not fJson.settingCache["keep_log"]:
            self.deleteTheLog()

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
        self.label_model_location_value["text"] = get_default_download_root()
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
