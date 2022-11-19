import sys
import tkinter as tk
import tkinter.ttk as ttk
from multiprocessing import Process


# User defined
sys.path.append("..")
from _version import __version__
from Globals import app_icon, app_name, fJson, gClass
from Logging import logger
from utils.DownloadModel import verify_model, download_model
from utils.Json import default_setting
from .MBox import Mbox
from .Tooltip import CreateToolTip


def notify(customTitle, customMessage, parent):
    Mbox(customTitle, customMessage, 0, parent)


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
        self.tabControl.add(self.frame_tab2, text="Model")

        self.frame_tab3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.frame_tab3, text="Translation")

        self.frame_tab4 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.frame_tab4, text="Textbox")

        # ------------------ Widgets - General ------------------
        # t1r1
        self.lf_t1r1 = ttk.LabelFrame(self.frame_tab1, text="Audio Capture")
        self.lf_t1r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.lf_t1r2 = ttk.LabelFrame(self.frame_tab1, text="Log")
        self.lf_t1r2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # cutoff
        # 1
        self.t1r1_1 = ttk.Frame(self.lf_t1r1)
        self.t1r1_1.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.label_cutOff_mic = ttk.Label(self.t1r1_1, text="Mic Cutoff: ")
        self.label_cutOff_mic.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_cutOff_mic, "Set the cut off length (in seconds) for microphone input.")

        self.spinner_cutOff_mic = ttk.Spinbox(self.t1r1_1, from_=3, to=30, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinner_cutOff_mic.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spinner_cutOff_mic, 30))
        self.spinner_cutOff_mic.pack(side=tk.LEFT, padx=5)

        self.label_cutOff_speaker = ttk.Label(self.t1r1_1, text="Speaker Cutoff: ")
        self.label_cutOff_speaker.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_cutOff_speaker, "Set the cut off length (in seconds) for speaker input.")

        self.spinner_cutOff_speaker = ttk.Spinbox(self.t1r1_1, from_=3, to=30, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinner_cutOff_speaker.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spinner_cutOff_speaker, 30))
        self.spinner_cutOff_speaker.pack(side=tk.LEFT, padx=5)

        # 2
        self.t1r1_2 = ttk.Frame(self.lf_t1r1)
        self.t1r1_2.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.label_separate_text_with = ttk.Label(self.t1r1_2, text="Text Separator: ")
        self.label_separate_text_with.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_separate_text_with, "Set the separator for text that is transcribed/translated.")

        self.entry_separate_text_with = ttk.Entry(self.t1r1_2)
        self.entry_separate_text_with.pack(side=tk.LEFT, padx=5)

        # 3
        self.t1r1_3 = ttk.Frame(self.lf_t1r1)
        self.t1r1_3.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.label_max_temp = ttk.Label(self.t1r1_3, text="Max Temp File: ")
        self.label_max_temp.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.label_max_temp, "Set max number of audio temp files before deletion in each recording session")

        self.spinner_max_temp = ttk.Spinbox(self.t1r1_3, from_=1, to=500, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.spinner_max_temp.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spinner_max_temp, 500))
        self.spinner_max_temp.pack(side=tk.LEFT, padx=5)

        self.checkbutton_keep_audio = ttk.Checkbutton(self.t1r1_3, text="Keep Audio")
        self.checkbutton_keep_audio.pack(side=tk.LEFT, padx=5)

        # log
        self.checkbutton_keep_log = ttk.Checkbutton(self.lf_t1r2, text="Keep Log")
        self.checkbutton_keep_log.pack(side=tk.LEFT, padx=5, pady=5)

        self.checkbutton_verbose = ttk.Checkbutton(self.lf_t1r2, text="Verbose Logging (Transcribed text)")
        self.checkbutton_verbose.pack(side=tk.LEFT, padx=5)

        # ------------------ Widgets - Model ------------------
        self.t2r1 = ttk.Frame(self.frame_tab2)
        self.t2r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t2r2 = ttk.Frame(self.frame_tab2)
        self.t2r2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # ------------------------------------
        # small
        self.t2r1_p1 = ttk.Frame(self.t2r1)
        self.t2r1_p1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_tiny = ttk.LabelFrame(self.t2r1_p1, text="Tiny")
        self.lf_model_tiny.pack(side=tk.LEFT)

        self.btn_interact_tiny = ttk.Button(self.lf_model_tiny, text="Verify", command=lambda: self.model_check("tiny", self.btn_interact_tiny))
        self.btn_interact_tiny.pack(side=tk.LEFT, padx=5)

        # ------------------------------------
        # small en
        self.t2r1_p2 = ttk.Frame(self.t2r1)
        self.t2r1_p2.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_tiny_eng = ttk.LabelFrame(self.t2r1_p2, text="Tiny (en)")
        self.lf_model_tiny_eng.pack(side=tk.LEFT)

        self.btn_interact_tiny_eng = ttk.Button(self.lf_model_tiny_eng, text="Verify", command=lambda: self.model_check("tiny.en", self.btn_interact_tiny_eng))
        self.btn_interact_tiny_eng.pack(side=tk.LEFT, padx=5)

        # ------------------------------------
        # base
        self.t2r1_p3 = ttk.Frame(self.t2r1)
        self.t2r1_p3.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_base = ttk.LabelFrame(self.t2r1_p3, text="Base")
        self.lf_model_base.pack(side=tk.LEFT)

        self.btn_interact_base = ttk.Button(self.lf_model_base, text="Verify", command=lambda: self.model_check("base", self.btn_interact_base))
        self.btn_interact_base.pack(side=tk.LEFT, padx=5)

        # ------------------------------------
        # base en
        self.t2r1_p4 = ttk.Frame(self.t2r1)
        self.t2r1_p4.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_base_eng = ttk.LabelFrame(self.t2r1_p4, text="Base (en)")
        self.lf_model_base_eng.pack(side=tk.LEFT)

        self.btn_interact_base_eng = ttk.Button(self.lf_model_base_eng, text="Verify", command=lambda: self.model_check("base.en", self.btn_interact_base_eng))
        self.btn_interact_base_eng.pack(side=tk.LEFT, padx=5)

        # ------------------------------------
        # small
        self.t2r1_p5 = ttk.Frame(self.t2r1)
        self.t2r1_p5.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_small = ttk.LabelFrame(self.t2r1_p5, text="Small")
        self.lf_model_small.pack(side=tk.LEFT)

        self.btn_interact_small = ttk.Button(self.lf_model_small, text="Verify", command=lambda: self.model_check("small", self.btn_interact_small))
        self.btn_interact_small.pack(side=tk.LEFT, padx=5)

        # ------------------------------------
        # small en
        self.t2r1_p6 = ttk.Frame(self.t2r1)
        self.t2r1_p6.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_small_eng = ttk.LabelFrame(self.t2r1_p6, text="Small (en)")
        self.lf_model_small_eng.pack(side=tk.LEFT)

        self.btn_interact_small_eng = ttk.Button(self.lf_model_small_eng, text="Verify", command=lambda: self.model_check("small.en", self.btn_interact_small_eng))
        self.btn_interact_small_eng.pack(side=tk.LEFT, padx=5)

        # ------------------------------------
        # medium
        self.t2r1_p7 = ttk.Frame(self.t2r1)
        self.t2r1_p7.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_medium = ttk.LabelFrame(self.t2r1_p7, text="Medium")
        self.lf_model_medium.pack(side=tk.LEFT)

        self.btn_interact_medium = ttk.Button(self.lf_model_medium, text="Verify", command=lambda: self.model_check("medium", self.btn_interact_medium))
        self.btn_interact_medium.pack(side=tk.LEFT, padx=5)

        # ------------------------------------
        # medium en
        self.t2r1_p8 = ttk.Frame(self.t2r1)
        self.t2r1_p8.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_medium_eng = ttk.LabelFrame(self.t2r1_p8, text="Medium (en)")
        self.lf_model_medium_eng.pack(side=tk.LEFT)

        self.btn_interact_medium_eng = ttk.Button(self.lf_model_medium_eng, text="Verify", command=lambda: self.model_check("medium.en", self.btn_interact_medium_eng))
        self.btn_interact_medium_eng.pack(side=tk.LEFT, padx=5)

        # ------------------------------------
        # large
        self.t2r1_p9 = ttk.Frame(self.t2r1)
        self.t2r1_p9.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.lf_model_large = ttk.LabelFrame(self.t2r1_p9, text="Large")
        self.lf_model_large.pack(side=tk.LEFT)

        self.btn_interact_large = ttk.Button(self.lf_model_large, text="Verify", command=lambda: self.model_check("large", self.btn_interact_large))
        self.btn_interact_large.pack(side=tk.LEFT, padx=5)

        # ------------------ Widgets - Translation ------------------
        self.lf_t3r1 = ttk.LabelFrame(self.frame_tab3, text="Libre Translate Setting")
        self.lf_t3r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.label_libre_key = ttk.Label(self.lf_t3r1, text="Libre Translate API Key")
        self.label_libre_key.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.label_libre_key, "Libre Translate API Key. Leave empty if not needed or host locally.")

        self.entry_libre_key = ttk.Entry(self.lf_t3r1)
        self.entry_libre_key.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_libre_host = ttk.Label(self.lf_t3r1, text="Libre Translate Host")
        self.label_libre_host.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_libre_host = ttk.Entry(self.lf_t3r1)
        self.entry_libre_host.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_libre_port = ttk.Label(self.lf_t3r1, text="Libre Translate Port")
        self.label_libre_port.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_libre_port = ttk.Entry(self.lf_t3r1)
        self.entry_libre_port.pack(side=tk.LEFT, padx=5, pady=5)

        self.checkbutton_libre_https = ttk.Checkbutton(self.lf_t3r1, text="Use HTTPS")
        self.checkbutton_libre_https.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkbutton_libre_https, "Don't use this if you're hosting locally.")

        # ------------------ Widgets - Textbox ------------------
        self.t4r1 = ttk.Frame(self.frame_tab4)
        self.t4r1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t4r2 = ttk.Frame(self.frame_tab4)
        self.t4r2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t4r3 = ttk.Frame(self.frame_tab4)
        self.t4r3.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t4r4 = ttk.Frame(self.frame_tab4)
        self.t4r4.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.t4r5 = ttk.Frame(self.frame_tab4)
        self.t4r5.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # mw tc
        self.label_mw_tc = ttk.LabelFrame(self.t4r1, text="Main Window Transcribed Textbox")
        self.label_mw_tc.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tc_max = ttk.Label(self.label_mw_tc, text="Max Length")
        self.label_mw_tc_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_max = ttk.Spinbox(self.label_mw_tc, from_=50, to=10_000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.entry_mw_tc_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.entry_mw_tc_max, 30))
        self.entry_mw_tc_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tc_font = ttk.Label(self.label_mw_tc, text="Font")
        self.label_mw_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_font = ttk.Entry(self.label_mw_tc)
        self.entry_mw_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tc_font_size = ttk.Label(self.label_mw_tc, text="Font Size")
        self.label_mw_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_font_size = ttk.Entry(self.label_mw_tc)
        self.entry_mw_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tc_font_color = ttk.Label(self.label_mw_tc, text="Font Color")
        self.label_mw_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_font_color = ttk.Entry(self.label_mw_tc)
        self.entry_mw_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tc_bg_color = ttk.Label(self.label_mw_tc, text="Background Color")
        self.label_mw_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tc_bg_color = ttk.Entry(self.label_mw_tc)
        self.entry_mw_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        # mw tl
        self.label_mw_tl = ttk.LabelFrame(self.t4r2, text="Main Window Translated Textbox")
        self.label_mw_tl.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tl_max = ttk.Label(self.label_mw_tl, text="Max Length")
        self.label_mw_tl_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_max = ttk.Spinbox(self.label_mw_tl, from_=50, to=10_000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.entry_mw_tl_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.entry_mw_tl_max, 30))
        self.entry_mw_tl_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tl_font = ttk.Label(self.label_mw_tl, text="Font")
        self.label_mw_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_font = ttk.Entry(self.label_mw_tl)
        self.entry_mw_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tl_font_size = ttk.Label(self.label_mw_tl, text="Font Size")
        self.label_mw_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_font_size = ttk.Entry(self.label_mw_tl)
        self.entry_mw_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tl_font_color = ttk.Label(self.label_mw_tl, text="Font Color")
        self.label_mw_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_font_color = ttk.Entry(self.label_mw_tl)
        self.entry_mw_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_mw_tl_bg_color = ttk.Label(self.label_mw_tl, text="Background Color")
        self.label_mw_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_tl_bg_color = ttk.Entry(self.label_mw_tl)
        self.entry_mw_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        # detached tc
        self.label_detached_tc = ttk.LabelFrame(self.t4r3, text="Detached Transcribed Window Textbox")
        self.label_detached_tc.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tc_max = ttk.Label(self.label_detached_tc, text="Max Length")
        self.label_detached_tc_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tc_max = ttk.Spinbox(self.label_detached_tc, from_=50, to=10_000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.entry_detached_tc_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.entry_detached_tc_max, 30))
        self.entry_detached_tc_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tc_font = ttk.Label(self.label_detached_tc, text="Font")
        self.label_detached_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tc_font = ttk.Entry(self.label_detached_tc)
        self.entry_detached_tc_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tc_font_size = ttk.Label(self.label_detached_tc, text="Font Size")
        self.label_detached_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tc_font_size = ttk.Entry(self.label_detached_tc)
        self.entry_detached_tc_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tc_font_color = ttk.Label(self.label_detached_tc, text="Font Color")
        self.label_detached_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tc_font_color = ttk.Entry(self.label_detached_tc)
        self.entry_detached_tc_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tc_bg_color = ttk.Label(self.label_detached_tc, text="Background Color")
        self.label_detached_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tc_bg_color = ttk.Entry(self.label_detached_tc)
        self.entry_detached_tc_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        # detached tl
        self.label_detached_tl = ttk.LabelFrame(self.t4r4, text="Detached Translated Window Textbox")
        self.label_detached_tl.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tl_max = ttk.Label(self.label_detached_tl, text="Max Length")
        self.label_detached_tl_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tl_max = ttk.Spinbox(self.label_detached_tl, from_=50, to=10_000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"))
        self.entry_detached_tl_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.entry_detached_tl_max, 30))
        self.entry_detached_tl_max.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tl_font = ttk.Label(self.label_detached_tl, text="Font")
        self.label_detached_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tl_font = ttk.Entry(self.label_detached_tl)
        self.entry_detached_tl_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tl_font_size = ttk.Label(self.label_detached_tl, text="Font Size")
        self.label_detached_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tl_font_size = ttk.Entry(self.label_detached_tl)
        self.entry_detached_tl_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tl_font_color = ttk.Label(self.label_detached_tl, text="Font Color")
        self.label_detached_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tl_font_color = ttk.Entry(self.label_detached_tl)
        self.entry_detached_tl_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_detached_tl_bg_color = ttk.Label(self.label_detached_tl, text="Background Color")
        self.label_detached_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_detached_tl_bg_color = ttk.Entry(self.label_detached_tl)
        self.entry_detached_tl_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        # button
        self.btn_reset_default = ttk.Button(self.t4r5, text="Reset to Default", command=self.reset_textbox_default)
        self.btn_reset_default.pack(side=tk.LEFT, padx=5, pady=5)

        # ------------------ Variables ------------------
        # Flags
        gClass.sw = self  # type: ignore Add self to global class

        # ------------------ Functions ------------------
        self.on_close()  # hide window on start
        self.checkModelOnStart()

    def on_close(self):
        self.root.withdraw()

    def on_open(self):
        self.root.deiconify()
        self.init_setting()

    def init_setting(self):
        self.spinner_cutOff_mic.set(fJson.settingCache["cutOff"]["mic"])
        self.spinner_cutOff_speaker.set(fJson.settingCache["cutOff"]["speaker"])
        self.entry_separate_text_with.insert(0, fJson.settingCache["separate_with"])
        self.spinner_max_temp.set(fJson.settingCache["max_temp"])

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

        self.entry_libre_key.insert(0, fJson.settingCache["libre_api_key"])
        self.entry_libre_host.insert(0, fJson.settingCache["libre_host"])
        self.entry_libre_port.insert(0, fJson.settingCache["libre_port"])

        if fJson.settingCache["libre_https"]:
            self.checkbutton_libre_https.invoke()
        else:
            self.checkbutton_libre_https.invoke()
            self.checkbutton_libre_https.invoke()

        self.entry_mw_tc_max.insert(0, fJson.settingCache["textbox"]["mw_tc"]["max"])
        self.entry_mw_tc_font.insert(0, fJson.settingCache["textbox"]["mw_tc"]["font"])
        self.entry_mw_tc_font_size.insert(0, fJson.settingCache["textbox"]["mw_tc"]["font_size"])
        self.entry_mw_tc_font_color.insert(0, fJson.settingCache["textbox"]["mw_tc"]["font_color"])
        self.entry_mw_tc_bg_color.insert(0, fJson.settingCache["textbox"]["mw_tc"]["bg_color"])

        self.entry_mw_tl_max.insert(0, fJson.settingCache["textbox"]["mw_tl"]["max"])
        self.entry_mw_tl_font.insert(0, fJson.settingCache["textbox"]["mw_tl"]["font"])
        self.entry_mw_tl_font_size.insert(0, fJson.settingCache["textbox"]["mw_tl"]["font_size"])
        self.entry_mw_tl_font_color.insert(0, fJson.settingCache["textbox"]["mw_tl"]["font_color"])
        self.entry_mw_tl_bg_color.insert(0, fJson.settingCache["textbox"]["mw_tl"]["bg_color"])

        self.entry_detached_tc_max.insert(0, fJson.settingCache["textbox"]["detached_tc"]["max"])
        self.entry_detached_tc_font.insert(0, fJson.settingCache["textbox"]["detached_tc"]["font"])
        self.entry_detached_tc_font_size.insert(0, fJson.settingCache["textbox"]["detached_tc"]["font_size"])
        self.entry_detached_tc_font_color.insert(0, fJson.settingCache["textbox"]["detached_tc"]["font_color"])
        self.entry_detached_tc_bg_color.insert(0, fJson.settingCache["textbox"]["detached_tc"]["bg_color"])

        self.entry_detached_tl_max.insert(0, fJson.settingCache["textbox"]["detached_tl"]["max"])
        self.entry_detached_tl_font.insert(0, fJson.settingCache["textbox"]["detached_tl"]["font"])
        self.entry_detached_tl_font_size.insert(0, fJson.settingCache["textbox"]["detached_tl"]["font_size"])
        self.entry_detached_tl_font_color.insert(0, fJson.settingCache["textbox"]["detached_tl"]["font_color"])
        self.entry_detached_tl_bg_color.insert(0, fJson.settingCache["textbox"]["detached_tl"]["bg_color"])

    def reset_textbox_default(self):
        self.entry_mw_tc_max.delete(0, tk.END)
        self.entry_mw_tc_max.insert(0, default_setting["textbox"]["mw_tc"]["max"])

        self.entry_mw_tc_font.delete(0, tk.END)
        self.entry_mw_tc_font.insert(0, default_setting["textbox"]["mw_tc"]["font"])

        self.entry_mw_tc_font_size.delete(0, tk.END)
        self.entry_mw_tc_font_size.insert(0, default_setting["textbox"]["mw_tc"]["font_size"])

        self.entry_mw_tc_font_color.delete(0, tk.END)
        self.entry_mw_tc_font_color.insert(0, default_setting["textbox"]["mw_tc"]["font_color"])

        self.entry_mw_tc_bg_color.delete(0, tk.END)
        self.entry_mw_tc_bg_color.insert(0, default_setting["textbox"]["mw_tc"]["bg_color"])

        self.entry_mw_tl_max.delete(0, tk.END)
        self.entry_mw_tl_max.insert(0, default_setting["textbox"]["mw_tl"]["max"])

        self.entry_mw_tl_font.delete(0, tk.END)
        self.entry_mw_tl_font.insert(0, default_setting["textbox"]["mw_tl"]["font"])

        self.entry_mw_tl_font_size.delete(0, tk.END)
        self.entry_mw_tl_font_size.insert(0, default_setting["textbox"]["mw_tl"]["font_size"])

        self.entry_mw_tl_font_color.delete(0, tk.END)
        self.entry_mw_tl_font_color.insert(0, default_setting["textbox"]["mw_tl"]["font_color"])

        self.entry_mw_tl_bg_color.delete(0, tk.END)
        self.entry_mw_tl_bg_color.insert(0, default_setting["textbox"]["mw_tl"]["bg_color"])

        self.entry_detached_tc_max.delete(0, tk.END)
        self.entry_detached_tc_max.insert(0, default_setting["textbox"]["detached_tc"]["max"])

        self.entry_detached_tc_font.delete(0, tk.END)
        self.entry_detached_tc_font.insert(0, default_setting["textbox"]["detached_tc"]["font"])

        self.entry_detached_tc_font_size.delete(0, tk.END)
        self.entry_detached_tc_font_size.insert(0, default_setting["textbox"]["detached_tc"]["font_size"])

        self.entry_detached_tc_font_color.delete(0, tk.END)
        self.entry_detached_tc_font_color.insert(0, default_setting["textbox"]["detached_tc"]["font_color"])

        self.entry_detached_tc_bg_color.delete(0, tk.END)
        self.entry_detached_tc_bg_color.insert(0, default_setting["textbox"]["detached_tc"]["bg_color"])

        self.entry_detached_tl_max.delete(0, tk.END)
        self.entry_detached_tl_max.insert(0, default_setting["textbox"]["detached_tl"]["max"])

        self.entry_detached_tl_font.delete(0, tk.END)
        self.entry_detached_tl_font.insert(0, default_setting["textbox"]["detached_tl"]["font"])

        self.entry_detached_tl_font_size.delete(0, tk.END)
        self.entry_detached_tl_font_size.insert(0, default_setting["textbox"]["detached_tl"]["font_size"])

        self.entry_detached_tl_font_color.delete(0, tk.END)
        self.entry_detached_tl_font_color.insert(0, default_setting["textbox"]["detached_tl"]["font_color"])

        self.entry_detached_tl_bg_color.delete(0, tk.END)
        self.entry_detached_tl_bg_color.insert(0, default_setting["textbox"]["detached_tl"]["bg_color"])

    def number_only(self, P):
        return P.isdigit()

    def verifyMaxNumber(self, el, max: int):
        value = el.get()

        if int(value) > max:
            el.set(max)

    def model_check(self, model: str, btn: ttk.Button) -> None:
        downloaded = verify_model(model)

        if not downloaded:
            notify("Model not found", "Model not found or checksum does not match. You can press download to download the model.", self.root)
            btn.config(text="Download", command=lambda: self.modelDownload(model, btn))
        else:
            btn.config(text="Downloaded", state=tk.DISABLED)

    def modelDownload(self, model: str, btn: ttk.Button) -> None:
        # if already downloading then return
        if gClass.dl_proc is not None:
            notify("Already downloading", "Please wait for the current download to finish.", self.root)
            return

        # Download model
        gClass.dl_proc = Process(target=download_model, args=(model,), daemon=True)
        gClass.dl_proc.start()

        # Update button
        btn.config(text="Downloading... (Click to cancel)", command=lambda: self.modelDownloadCancel(model, btn))

        # notify
        notify("Downloading model...", "Check the log for more information", self.root)

    def modelDownloadCancel(self, model: str, btn: ttk.Button) -> None:
        # Kill process
        if gClass.dl_proc is not None:
            gClass.dl_proc.terminate()
            gClass.dl_proc = None

        # Update button
        btn.config(text="Download", command=lambda: self.modelDownload(model, btn))

        # notify
        notify("Download cancelled.", "Model download cancelled.", self.root)

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
