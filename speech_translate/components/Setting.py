import os
import platform
from time import sleep
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
        self.tabControl.add(self.ft2, text="Transcribe & Translate")

        self.ft3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft3, text="Textbox")

        self.ft4 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft4, text="Other")

        # ------------------ Widgets - General ------------------
        # log
        self.ft1_logging = tk.LabelFrame(self.ft1, text="• Logging")
        self.ft1_logging.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t1_logging_1 = ttk.Frame(self.ft1_logging)
        self.t1_logging_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.lbl_log_location = ttk.Label(self.t1_logging_1, text="Log Files Location ", width=16)
        self.lbl_log_location.pack(side=tk.LEFT, padx=5)

        self.entry_log_location_value = ttk.Entry(self.t1_logging_1, cursor="hand2", width=100)
        self.entry_log_location_value.insert(0, dir_log)
        self.entry_log_location_value.config(state="readonly")
        self.entry_log_location_value.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_log_location_value.bind("<Button-1>", lambda e: startFile(dir_log))
        self.entry_log_location_value.bind("<Button-3>", lambda e: self.promptDeleteLog())
        CreateToolTip(self.entry_log_location_value, "Location of log file.\n- LClick to open the folder.\n- RClick to delete all log files.")

        self.t1_logging_2 = ttk.Frame(self.ft1_logging)
        self.t1_logging_2.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.cbtn_keep_log = ttk.Checkbutton(self.t1_logging_2, text="Keep Log Files", command=lambda: fJson.savePartialSetting("keep_log", self.cbtn_keep_log.instate(["selected"])))
        self.cbtn_keep_log.pack(side=tk.LEFT, padx=5, pady=5)

        self.cbtn_verbose = ttk.Checkbutton(self.t1_logging_2, text="Verbose Logging for Whisper", command=lambda: fJson.savePartialSetting("verbose", self.cbtn_verbose.instate(["selected"])))
        self.cbtn_verbose.pack(side=tk.LEFT, padx=5)

        # only on windows
        if platform.system() == "Windows":
            self.cbtn_hide_console_window_on_start = ttk.Checkbutton(
                self.t1_logging_2, text="Hide Console Window on Start", command=lambda: fJson.savePartialSetting("hide_console_window_on_start", self.cbtn_hide_console_window_on_start.instate(["selected"]))
            )
            self.cbtn_hide_console_window_on_start.pack(side=tk.LEFT, padx=5)
            CreateToolTip(self.cbtn_hide_console_window_on_start, "Will hide console (log) window every program start. Only on Windows.")

        # model
        self.ft1_model = tk.LabelFrame(self.ft1, text="• Model")
        self.ft1_model.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # label model location
        self.t1_model_1 = ttk.Frame(self.ft1_model)
        self.t1_model_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.lbl_model_location = ttk.Label(self.t1_model_1, text="Model Location ", width=16)
        self.lbl_model_location.pack(side=tk.LEFT, padx=5)

        self.entry_model_location_value = ttk.Entry(self.t1_model_1, cursor="hand2", width=100)
        self.entry_model_location_value.insert(0, get_default_download_root())
        self.entry_model_location_value.config(state="readonly")
        self.entry_model_location_value.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_model_location_value.bind("<Button-1>", lambda e: startFile(self.entry_model_location_value.cget("text")))
        CreateToolTip(self.entry_model_location_value, "Location of the model file.\nLClick to open the folder")

        # the models
        self.t1_model_2 = ttk.Frame(self.ft1_model)
        self.t1_model_2.pack(side=tk.TOP, fill=tk.X)

        # small
        self.lf_md_dl1 = ttk.Frame(self.t1_model_2)
        self.lf_md_dl1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_tiny = ttk.LabelFrame(self.lf_md_dl1, text="Tiny")
        self.lf_model_tiny.pack(side=tk.LEFT)

        self.btn_interact_tiny = ttk.Button(self.lf_model_tiny, text="Verify", command=lambda: self.model_check("tiny", self.btn_interact_tiny))
        self.btn_interact_tiny.pack(side=tk.LEFT, padx=5)

        # small en
        self.lf_md_dl2 = ttk.Frame(self.t1_model_2)
        self.lf_md_dl2.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_tiny_eng = ttk.LabelFrame(self.lf_md_dl2, text="Tiny (en)")
        self.lf_model_tiny_eng.pack(side=tk.LEFT)

        self.btn_interact_tiny_eng = ttk.Button(self.lf_model_tiny_eng, text="Verify", command=lambda: self.model_check("tiny.en", self.btn_interact_tiny_eng))
        self.btn_interact_tiny_eng.pack(side=tk.LEFT, padx=5)

        # base
        self.lf_md_dl3 = ttk.Frame(self.t1_model_2)
        self.lf_md_dl3.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_base = ttk.LabelFrame(self.lf_md_dl3, text="Base")
        self.lf_model_base.pack(side=tk.LEFT)

        self.btn_interact_base = ttk.Button(self.lf_model_base, text="Verify", command=lambda: self.model_check("base", self.btn_interact_base))
        self.btn_interact_base.pack(side=tk.LEFT, padx=5)

        # base en
        self.lf_md_dl4 = ttk.Frame(self.t1_model_2)
        self.lf_md_dl4.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_base_eng = ttk.LabelFrame(self.lf_md_dl4, text="Base (en)")
        self.lf_model_base_eng.pack(side=tk.LEFT)

        self.btn_interact_base_eng = ttk.Button(self.lf_model_base_eng, text="Verify", command=lambda: self.model_check("base.en", self.btn_interact_base_eng))
        self.btn_interact_base_eng.pack(side=tk.LEFT, padx=5)

        # small
        self.lf_md_dl5 = ttk.Frame(self.t1_model_2)
        self.lf_md_dl5.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_small = ttk.LabelFrame(self.lf_md_dl5, text="Small")
        self.lf_model_small.pack(side=tk.LEFT)

        self.btn_interact_small = ttk.Button(self.lf_model_small, text="Verify", command=lambda: self.model_check("small", self.btn_interact_small))
        self.btn_interact_small.pack(side=tk.LEFT, padx=5)

        # small en
        self.lf_md_dl6 = ttk.Frame(self.t1_model_2)
        self.lf_md_dl6.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_small_eng = ttk.LabelFrame(self.lf_md_dl6, text="Small (en)")
        self.lf_model_small_eng.pack(side=tk.LEFT)

        self.btn_interact_small_eng = ttk.Button(self.lf_model_small_eng, text="Verify", command=lambda: self.model_check("small.en", self.btn_interact_small_eng))
        self.btn_interact_small_eng.pack(side=tk.LEFT, padx=5)

        # medium
        self.lf_md_dl7 = ttk.Frame(self.t1_model_2)
        self.lf_md_dl7.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_medium = ttk.LabelFrame(self.lf_md_dl7, text="Medium")
        self.lf_model_medium.pack(side=tk.LEFT)

        self.btn_interact_medium = ttk.Button(self.lf_model_medium, text="Verify", command=lambda: self.model_check("medium", self.btn_interact_medium))
        self.btn_interact_medium.pack(side=tk.LEFT, padx=5)

        # medium en
        self.lf_md_dl8 = ttk.Frame(self.t1_model_2)
        self.lf_md_dl8.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_medium_eng = ttk.LabelFrame(self.lf_md_dl8, text="Medium (en)")
        self.lf_model_medium_eng.pack(side=tk.LEFT)

        self.btn_interact_medium_eng = ttk.Button(self.lf_model_medium_eng, text="Verify", command=lambda: self.model_check("medium.en", self.btn_interact_medium_eng))
        self.btn_interact_medium_eng.pack(side=tk.LEFT, padx=5)

        # large
        self.lf_md_dl9 = ttk.Frame(self.t1_model_2)
        self.lf_md_dl9.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_large = ttk.LabelFrame(self.lf_md_dl9, text="Large")
        self.lf_model_large.pack(side=tk.LEFT)

        self.btn_interact_large = ttk.Button(self.lf_model_large, text="Verify", command=lambda: self.model_check("large", self.btn_interact_large))
        self.btn_interact_large.pack(side=tk.LEFT, padx=5)

        # ------------------ Widgets - Translation ------------------
        self.ft2_tc = tk.LabelFrame(self.ft2, text="• Transcribe")
        self.ft2_tc.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        #
        self.tc_1 = ttk.Frame(self.ft2_tc)
        self.tc_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.tc_2 = ttk.Frame(self.ft2_tc)
        self.tc_2.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.tc_3 = ttk.Frame(self.ft2_tc)
        self.tc_3.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.tc_4 = ttk.Frame(self.ft2_tc)
        self.tc_4.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.tc_5 = ttk.Frame(self.ft2_tc)
        self.tc_5.pack(side=tk.TOP, fill=tk.X, pady=5)

        # 1
        self.lbl_separate_text_with = ttk.Label(self.tc_1, text="Text Separator", width=18)
        self.lbl_separate_text_with.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_separate_text_with, "Set the separator for text that is transcribed or translated.\n\n. - Default value \\n", wrapLength=400)

        self.entry_separate_text_with = ttk.Entry(self.tc_1, width=22)
        self.entry_separate_text_with.pack(side=tk.LEFT, padx=5)
        self.entry_separate_text_with.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("separate_with", self.entry_separate_text_with.get()))
        CreateToolTip(self.entry_separate_text_with, "Set the separator for text that is transcribed or translated.\n\nDefault value \\n", wrapLength=400)

        self.lbl_max_temp = ttk.Label(self.tc_1, text="Max sentences", width=18)
        self.lbl_max_temp.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_max_temp, "Set max number of sentences kept between each buffer reset. Default value is 5.")

        self.spn_max_sentences = ttk.Spinbox(
            self.tc_1, from_=1, to=30, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: fJson.savePartialSetting("max_sentences", int(self.spn_max_sentences.get()))
        )
        self.spn_max_sentences.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_max_sentences, 1, 30, lambda: fJson.savePartialSetting("max_sentences", int(self.spn_max_sentences.get()))))
        self.spn_max_sentences.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spn_max_sentences, "Set max number of sentences kept between each buffer reset. Default value is 5.")

        # 2
        self.lbl_sample_rate = ttk.Label(self.tc_2, text="Sample Rate", width=18)
        self.lbl_sample_rate.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_sample_rate, "Set the sample rate for the audio recording. Default value is 16000.")

        self.spn_sample_rate = ttk.Spinbox(
            self.tc_2, from_=8000, to=48000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: fJson.savePartialSetting("sample_rate", int(self.spn_sample_rate.get()))
        )
        self.spn_sample_rate.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_sample_rate, 8000, 48000, lambda: fJson.savePartialSetting("sample_rate", int(self.spn_sample_rate.get()))))
        self.spn_sample_rate.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spn_sample_rate, "Set the sample rate for the audio recording. Default value is 16000.")

        self.lbl_chunk_size = ttk.Label(self.tc_2, text="Chunk size", width=18)
        self.lbl_chunk_size.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_chunk_size, "Set the chunk size for the audio recording. Default value is 1024.")

        self.spn_chunk_size = ttk.Spinbox(
            self.tc_2, from_=1024, to=65536, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: fJson.savePartialSetting("chunk", int(self.spn_chunk_size.get()))
        )
        self.spn_chunk_size.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_chunk_size, 1024, 65536, lambda: fJson.savePartialSetting("chunk", int(self.spn_chunk_size.get()))))
        self.spn_chunk_size.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spn_chunk_size, "Set the chunk size for the audio recording. Default value is 1024.")

        # 3
        self.lbl_tc_rate = ttk.Label(self.tc_3, text="Transcribe rate (ms)", width=18)
        self.lbl_tc_rate.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_tc_rate, "Set the transcribe rate or the time between each transcribe check. Default value is 500ms.\n\nThe lower the value, the more resource it will use.")

        self.spn_tc_rate = ttk.Spinbox(
            self.tc_3, from_=100, to=1000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: fJson.savePartialSetting("transcribe_rate", int(self.spn_tc_rate.get()))
        )

        self.spn_tc_rate.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_tc_rate, 100, 1000, lambda: fJson.savePartialSetting("transcribe_rate", int(self.spn_tc_rate.get()))))
        self.spn_tc_rate.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spn_tc_rate, "Set the transcribe rate or the time between each transcribe check. Default value is 500ms.\n\nThe lower the value, the more resource it will use.")

        # 4
        self.lbl_buffer = ttk.Label(self.tc_4, text="Max Buffer (seconds)", font="TkDefaultFont 9 bold")
        self.lbl_buffer.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_buffer, "Max buffer is the maximum continous recording time. After it is reached buffer will be reset.")

        # 3
        self.lbl_buffer_mic = ttk.Label(self.tc_5, text="Mic", width=18)
        self.lbl_buffer_mic.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_buffer_mic, "Set the max buffer (in seconds) for microphone input. Default value is 30 seconds.")

        self.spn_buffer_mic = ttk.Spinbox(
            self.tc_5,
            from_=3,
            to=300,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("mic_maxBuffer", int(self.spn_buffer_mic.get())),
        )
        self.spn_buffer_mic.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(self.spn_buffer_mic, 3, 300, lambda: fJson.savePartialSetting("mic_maxBuffer", int(self.spn_buffer_mic.get()))),
        )
        self.spn_buffer_mic.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spn_buffer_mic, "Set the max buffer (in seconds) for microphone input. Default value is 30 seconds.")

        self.lbl_buffer_speaker = ttk.Label(self.tc_5, text="Speaker", width=18)
        self.lbl_buffer_speaker.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.lbl_buffer_speaker, "Set the max buffer (in seconds) for speaker input. Default value is 45 seconds.")

        self.spn_buffer_speaker = ttk.Spinbox(
            self.tc_5,
            from_=3,
            to=300,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: fJson.savePartialSetting("speaker_maxBuffer", int(self.spn_buffer_speaker.get())),
        )
        self.spn_buffer_speaker.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(self.spn_buffer_speaker, 3, 300, lambda: fJson.savePartialSetting("speaker_maxBuffer", int(self.spn_buffer_speaker.get()))),
        )
        self.spn_buffer_speaker.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.spn_buffer_speaker, "Set the max buffer (in seconds) for speaker input. Default value is 45 seconds.")

        # translate
        self.ft2_tl = tk.LabelFrame(self.ft2, text="• Libre Translate Setting")
        self.ft2_tl.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.tl_1 = ttk.Frame(self.ft2_tl)
        self.tl_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.lbl_libre_key = ttk.Label(self.tl_1, text="Libre Translate API Key")
        self.lbl_libre_key.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_libre_key, "Libre Translate API Key. Leave empty if not needed or host locally.")

        self.entry_libre_key = ttk.Entry(self.tl_1)
        self.entry_libre_key.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_libre_key.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_api_key", self.entry_libre_key.get()))

        self.lbl_libre_host = ttk.Label(self.tl_1, text="Libre Translate Host")
        self.lbl_libre_host.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_libre_host = ttk.Entry(self.tl_1)
        self.entry_libre_host.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_libre_host.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_host", self.entry_libre_host.get()))

        self.lbl_libre_port = ttk.Label(self.tl_1, text="Libre Translate Port")
        self.lbl_libre_port.pack(side=tk.LEFT, padx=5, pady=5)
        self.lbl_libre_port.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_port", self.entry_libre_port.get()))

        self.entry_libre_port = ttk.Entry(self.tl_1)
        self.entry_libre_port.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_libre_port.bind("<KeyRelease>", lambda e: fJson.savePartialSetting("libre_port", self.entry_libre_port.get()))

        self.cbtn_libre_https = ttk.Checkbutton(self.tl_1, text="Use HTTPS", command=lambda: fJson.savePartialSetting("libre_https", self.cbtn_libre_https.instate(["selected"])))
        self.cbtn_libre_https.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_libre_https, "Don't use this if you're hosting locally.")

        # ------------------ Widgets - Textbox ------------------
        self.ft3_r1 = ttk.Frame(self.ft3)
        self.ft3_r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

        self.ft3_r2 = ttk.Frame(self.ft3)
        self.ft3_r2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

        self.ft3_r3 = ttk.Frame(self.ft3)
        self.ft3_r3.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

        self.ft3_r4 = ttk.Frame(self.ft3)
        self.ft3_r4.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

        self.ft3_r5 = ttk.Frame(self.ft3)
        self.ft3_r5.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=5, expand=True)

        # mw tc
        self.lf_mw_tc = tk.LabelFrame(self.ft3_r1, text="• Main Window Transcribed Textbox")
        self.lf_mw_tc.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_mw_tc_max = ttk.Label(self.lf_mw_tc, text="Max Length")
        self.lbl_mw_tc_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_mw_tc_max, "Maximum length of the textbox. 0 = no limit.")

        self.spn_mw_tc_max = ttk.Spinbox(
            self.lf_mw_tc,
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

        self.lbl_mw_tc_font = ttk.Label(self.lf_mw_tc, text="Font")
        self.lbl_mw_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_mw_tc_font = ttk.Combobox(self.lf_mw_tc, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tc_font.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_mw_tc_font.bind("<<ComboboxSelected>>", lambda e: fJson.savePartialSetting("tb_mw_tc_font", self.cb_mw_tc_font.get()) or self.preview_changes_tb())

        self.lbl_mw_tc_font_size = ttk.Label(self.lf_mw_tc, text="Font Size")
        self.lbl_mw_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spn_mw_tc_font_size = ttk.Spinbox(
            self.lf_mw_tc,
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

        self.lbl_mw_tc_font_color = ttk.Label(self.lf_mw_tc, text="Font Color")
        self.lbl_mw_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_font_color = ttk.Entry(self.lf_mw_tc, width=10)
        self.entry_mw_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tc_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_mw_tc_font_color, self.entry_mw_tc_font_color.get(), self.root)
            or fJson.savePartialSetting("tb_mw_tc_font_color", self.entry_mw_tc_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_mw_tc_font_color.bind("<Key>", lambda e: "break")

        self.lbl_mw_tc_bg_color = ttk.Label(self.lf_mw_tc, text="Background Color")
        self.lbl_mw_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_bg_color = ttk.Entry(self.lf_mw_tc, width=10)
        self.entry_mw_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tc_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_mw_tc_bg_color, self.entry_mw_tc_bg_color.get(), self.root) or fJson.savePartialSetting("tb_mw_tc_bg_color", self.entry_mw_tc_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_mw_tc_bg_color.bind("<Key>", lambda e: "break")

        # mw tl
        self.lf_mw_tl = tk.LabelFrame(self.ft3_r2, text="• Main Window Translated Textbox")
        self.lf_mw_tl.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_mw_tl_max = ttk.Label(self.lf_mw_tl, text="Max Length")
        self.lbl_mw_tl_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_mw_tl_max, "Maximum length of the textbox. 0 = no limit.")

        self.spn_mw_tl_max = ttk.Spinbox(
            self.lf_mw_tl,
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

        self.lbl_mw_tl_font = ttk.Label(self.lf_mw_tl, text="Font")
        self.lbl_mw_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_mw_tl_font = ttk.Combobox(self.lf_mw_tl, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tl_font.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_mw_tl_font.bind("<<ComboboxSelected>>", lambda e: fJson.savePartialSetting("tb_mw_tl_font", self.cb_mw_tl_font.get()) or self.preview_changes_tb())

        self.lbl_mw_tl_font_size = ttk.Label(self.lf_mw_tl, text="Font Size")
        self.lbl_mw_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spn_mw_tl_font_size = ttk.Spinbox(
            self.lf_mw_tl,
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

        self.lbl_mw_tl_font_color = ttk.Label(self.lf_mw_tl, text="Font Color")
        self.lbl_mw_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_font_color = ttk.Entry(self.lf_mw_tl, width=10)
        self.entry_mw_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tl_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_mw_tl_font_color, self.entry_mw_tl_font_color.get(), self.root)
            or fJson.savePartialSetting("tb_mw_tl_font_color", self.entry_mw_tl_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_mw_tl_font_color.bind("<Key>", lambda e: "break")

        self.lbl_mw_tl_bg_color = ttk.Label(self.lf_mw_tl, text="Background Color")
        self.lbl_mw_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_bg_color = ttk.Entry(self.lf_mw_tl, width=10)
        self.entry_mw_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_tl_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_mw_tl_bg_color, self.entry_mw_tl_bg_color.get(), self.root) or fJson.savePartialSetting("tb_mw_tl_bg_color", self.entry_mw_tl_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_mw_tl_bg_color.bind("<Key>", lambda e: "break")

        # detached tc
        self.lf_ex_tc = tk.LabelFrame(self.ft3_r3, text="• Detached Transcribed Window Textbox")
        self.lf_ex_tc.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_ex_tc_max = ttk.Label(self.lf_ex_tc, text="Max Length")
        self.lbl_ex_tc_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_ex_tc_max, "Maximum length of the textbox. 0 = no limit.")

        self.spn_ex_tc_max = ttk.Spinbox(
            self.lf_ex_tc,
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

        self.lbl_ex_tc_font = ttk.Label(self.lf_ex_tc, text="Font")
        self.lbl_ex_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_ex_tc_font = ttk.Combobox(self.lf_ex_tc, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_ex_tc_font_size = ttk.Label(self.lf_ex_tc, text="Font Size")
        self.lbl_ex_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spn_ex_tc_font_size = ttk.Spinbox(
            self.lf_ex_tc,
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

        self.lbl_ex_tc_font_color = ttk.Label(self.lf_ex_tc, text="Font Color")
        self.lbl_ex_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_tc_font_color = ttk.Entry(self.lf_ex_tc, width=10)
        self.entry_ex_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_tc_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_font_color, self.entry_ex_tc_font_color.get(), self.root)
            or fJson.savePartialSetting("tb_ex_tc_font_color", self.entry_ex_tc_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tc_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tc_bg_color = ttk.Label(self.lf_ex_tc, text="Background Color")
        self.lbl_ex_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_tc_bg_color = ttk.Entry(self.lf_ex_tc, width=10)
        self.entry_ex_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_tc_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_bg_color, self.entry_ex_tc_bg_color.get(), self.root) or fJson.savePartialSetting("tb_ex_tc_bg_color", self.entry_ex_tc_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tc_bg_color.bind("<Key>", lambda e: "break")

        # detached tl
        self.lf_ex_tl = tk.LabelFrame(self.ft3_r4, text="• Detached Translated Window Textbox")
        self.lf_ex_tl.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_ex_tl_max = ttk.Label(self.lf_ex_tl, text="Max Length")
        self.lbl_ex_tl_max.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_ex_tl_max, "Maximum length of the textbox. 0 = no limit.")

        self.spn_ex_tl_max = ttk.Spinbox(
            self.lf_ex_tl,
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

        self.lbl_ex_tl_font = ttk.Label(self.lf_ex_tl, text="Font")
        self.lbl_ex_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_ex_tl_font = ttk.Combobox(self.lf_ex_tl, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_ex_tl_font_size = ttk.Label(self.lf_ex_tl, text="Font Size")
        self.lbl_ex_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.spn_ex_tl_font_size = ttk.Spinbox(
            self.lf_ex_tl,
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

        self.lbl_ex_tl_font_color = ttk.Label(self.lf_ex_tl, text="Font Color")
        self.lbl_ex_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_tl_font_color = ttk.Entry(self.lf_ex_tl, width=10)
        self.entry_ex_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_tl_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_font_color, self.entry_ex_tl_font_color.get(), self.root)
            or fJson.savePartialSetting("tb_ex_tl_font_color", self.entry_ex_tl_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tl_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tl_bg_color = ttk.Label(self.lf_ex_tl, text="Background Color")
        self.lbl_ex_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_tl_bg_color = ttk.Entry(self.lf_ex_tl, width=10)
        self.entry_ex_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_tl_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_bg_color, self.entry_ex_tl_bg_color.get(), self.root) or fJson.savePartialSetting("tb_ex_tl_bg_color", self.entry_ex_tl_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tl_bg_color.bind("<Key>", lambda e: "break")

        # button
        self.tb_preview_1 = tk.Text(
            self.ft3_r5,
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
            self.ft3_r5,
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
            self.ft3_r5,
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
            self.ft3_r5,
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
        self.ft4_r1 = ttk.Frame(self.ft4)
        self.ft4_r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.lf_application = tk.LabelFrame(self.ft4_r1, text="• Application")
        self.lf_application.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        # check for update on start
        self.check_update_on_start = ttk.Checkbutton(
            self.lf_application, text="Check for update on start", command=lambda: fJson.savePartialSetting("checkUpdateOnStart", self.check_update_on_start.instate(["selected"]))
        )
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
        self.spn_buffer_mic.set(fJson.settingCache["mic_maxBuffer"])
        self.spn_buffer_speaker.set(fJson.settingCache["speaker_maxBuffer"])
        self.spn_max_sentences.set(fJson.settingCache["max_sentences"])
        self.spn_sample_rate.set(fJson.settingCache["sample_rate"])
        self.spn_chunk_size.set(fJson.settingCache["chunk_size"])
        self.spn_tc_rate.set(fJson.settingCache["transcribe_rate"])

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
        # verify value only after user has finished typing
        self.root.after(1000, lambda: self.checkNumber(el, min, max, cb_func))

    def checkNumber(self, el, min: int, max: int, cb_func=None):
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
