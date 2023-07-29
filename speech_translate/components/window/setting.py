import os
import platform
import threading
import random
import tkinter as tk
from tkinter import ttk, font, colorchooser, filedialog
from typing import Literal

from speech_translate._path import app_icon
from speech_translate._contants import APP_NAME, PREVIEW_WORDS
from speech_translate.globals import sj, gc, dir_log, dir_temp, dir_export
from speech_translate.custom_logging import logger, current_log
from speech_translate.utils.helper import chooseColor
from speech_translate.utils.model_download import verify_model, download_model, get_default_download_root
from speech_translate.utils.helper import startFile, cbtnInvoker
from speech_translate.utils.helper_whisper import convert_str_options_to_dict, get_temperature
from speech_translate.utils.record import getDeviceAverageThreshold
from speech_translate.utils.style import set_ui_style
from speech_translate.components.custom.countdown import CountdownWindow
from speech_translate.components.custom.message import mbox, MBoxText
from speech_translate.components.custom.tooltip import CreateToolTip, createMultipleTooltips, CreateToolTipOnText




class SettingWindow:
    """
    Setting UI
    """

    def __init__(self, master: tk.Tk):
        self.root = tk.Toplevel(master)

        self.root.title(APP_NAME + " | Settings")
        self.root.geometry(sj.cache["sw_size"])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.wm_attributes("-topmost", False)  # Default False

        self.fonts = list(font.families())
        self.fonts.append("TKDefaultFont")
        self.fonts.sort()
        self.initial_theme = ""
        self.getting_threshold = False
        self.model_checked = False
        self.checkingModel = False
        self.first_check = True

        # ------------------ Frames ------------------
        self.frame_top = tk.Frame(self.root)
        self.frame_top.pack(side="top", fill="x")

        self.frame_bottom = tk.Frame(self.root)
        self.frame_bottom.pack(side="bottom", fill="x")

        # ------------------ Widgets ------------------
        # notebook
        self.tabControl = ttk.Notebook(self.frame_top)
        self.tabControl.pack(fill="both", expand=True)

        self.ft_general = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft_general, text="General")
        self.ft_general.bind("<Button-1>", lambda event: self.root.focus_set())

        self.ft_transcribe = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft_transcribe, text="Transcribe")
        self.ft_transcribe.bind("<Button-1>", lambda event: self.root.focus_set())

        self.ft_translate = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft_translate, text="Translate")
        self.ft_translate.bind("<Button-1>", lambda event: self.root.focus_set())

        self.ft_textbox = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft_textbox, text="Textbox")
        self.ft_textbox.bind("<Button-1>", lambda event: self.root.focus_set())

        # ------------------ General ------------------
        # app
        self.lf_application = tk.LabelFrame(self.ft_general, text="• Application")
        self.lf_application.pack(side="top", fill="x", padx=5, pady=5)

        self.f_application_1 = ttk.Frame(self.lf_application)
        self.f_application_1.pack(side="top", fill="x", padx=5)

        self.f_application_2 = ttk.Frame(self.lf_application)
        self.f_application_2.pack(side="top", fill="x", padx=5)

        self.f_application_3 = ttk.Frame(self.lf_application)
        self.f_application_3.pack(side="top", fill="x", padx=5)

        self.cbtn_update_on_start = ttk.Checkbutton(
            self.f_application_1, text="Check for update on start", command=lambda: sj.savePartialSetting("checkUpdateOnStart", self.cbtn_update_on_start.instate(["selected"])), style="Switch.TCheckbutton"
        )
        self.cbtn_update_on_start.pack(side="left", padx=5, pady=5)

        self.cbtn_supress_hidden_to_tray = ttk.Checkbutton(
            self.f_application_1,
            text="Supress hidden to tray notif",
            command=lambda: sj.savePartialSetting("supress_hidden_to_tray", self.cbtn_supress_hidden_to_tray.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_supress_hidden_to_tray.pack(side="left", padx=5, pady=5)

        self.cbtn_supress_device_warning = ttk.Checkbutton(
            self.f_application_1,
            text="Supress device warning",
            command=lambda: sj.savePartialSetting("supress_device_warning", self.cbtn_supress_device_warning.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_supress_device_warning.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.cbtn_supress_device_warning, "Supress warning notification that usually shows up when no input device is detected.")

        self.lbl_notice_theme = ttk.Label(self.f_application_1, text="— Might need to reload the app for the changes to take effect.")
        self.lbl_notice_theme.pack(side="left", padx=5, pady=5)

        # theme
        self.lbl_theme = ttk.Label(self.f_application_2, text="Theme")
        self.lbl_theme.pack(side="left", padx=5, pady=5)
        CreateToolTip(
            self.lbl_theme,
            "Set theme for app.\nThe topmost selection is your default tkinter os theme.\n\nTo add custom theme you can read the readme.txt in the theme folder.\n\nMight need to reload the app for the changes to take effect.",
            wrapLength=500,
        )

        self.cb_theme = ttk.Combobox(self.f_application_2, values=["dummy list"], state="readonly")
        self.cb_theme.pack(side="left", padx=5, pady=5)
        self.cb_theme.bind("<<ComboboxSelected>>", self.cb_theme_change)
        CreateToolTip(
            self.cb_theme,
            "Set theme for app.\nThe topmost selection is your default tkinter os theme.\n\nTo add custom theme you can read the readme.txt in the theme folder.\n\nMight need to reload the app for the changes to take effect.",
            wrapLength=500,
        )

        self.entry_theme = ttk.Entry(self.f_application_2)
        self.entry_theme.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        CreateToolTip(
            self.entry_theme,
            "Set the custom theme name if the one from dropdown is not working.\n\nThe theme name should be according to the `set_theme` parameter in the .tcl folder of the theme.\n\nMight need to reload the app for the changes to take effect.",
            wrapLength=500,
        )

        self.btn_theme_add = ttk.Button(self.f_application_2, text="Add", command=self.add_theme)
        self.btn_theme_add.pack(side="left", padx=5, pady=5)
        CreateToolTip(
            self.btn_theme_add,
            "Add custom theme.\n\nThe theme name should be according to the `set_theme` parameter in the .tcl folder of the theme.\n\nMight need to reload the app for the changes to take effect.",
            wrapLength=500,
        )

        # --------------------
        # export
        self.lf_export = tk.LabelFrame(self.ft_general, text="• Export")
        self.lf_export.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_1 = ttk.Frame(self.lf_export)
        self.f_export_1.pack(side="top", fill="x", padx=5)

        self.f_export_2 = ttk.Frame(self.lf_export)
        self.f_export_2.pack(side="top", fill="x", padx=5)

        self.f_export_3 = ttk.Frame(self.lf_export)
        self.f_export_3.pack(side="top", fill="x", padx=5)

        self.lbl_export = ttk.Label(self.f_export_1, text="Export Folder", width=16)
        self.lbl_export.pack(side="left", padx=5, pady=5)

        self.entry_export = ttk.Entry(self.f_export_1, cursor="hand2")
        self.entry_export.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.entry_export.bind("<Button-1>", lambda event: self.change_export_path())
        self.entry_export.bind("<Button-3>", lambda event: self.default_export_path())
        CreateToolTip(self.entry_export, "The folder where exported text from import file are saved.\n\n- LClick the button to change the folder.\n- RClick to set back to default.")

        self.cbtn_auto_open_export = ttk.Checkbutton(
            self.f_export_2, text="Auto open export folder", command=lambda: sj.savePartialSetting("auto_open_dir_export", self.cbtn_auto_open_export.instate(["selected"])), style="Switch.TCheckbutton"
        )
        self.cbtn_auto_open_export.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.cbtn_auto_open_export, "Auto open the export folder after file import")

        self.btn_open_export_folder = ttk.Button(self.f_export_3, text="Open Export Folder", command=lambda: startFile(dir_export))
        self.btn_open_export_folder.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.btn_open_export_folder, "Open the folder where exported text from import file are saved.")

        self.btn_delete_export_folder = ttk.Button(self.f_export_3, text="Clear Export Folder", command=self.clear_export)
        self.btn_delete_export_folder.pack(side="left", padx=5, pady=5)

        # --------------------
        # log
        self.lf_logging = tk.LabelFrame(self.ft_general, text="• Logging")
        self.lf_logging.pack(side="top", fill="x", padx=5, pady=5)

        self.f_logging_1 = ttk.Frame(self.lf_logging)
        self.f_logging_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_2 = ttk.Frame(self.lf_logging)
        self.f_logging_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_3 = ttk.Frame(self.lf_logging)
        self.f_logging_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_4 = ttk.Frame(self.lf_logging)
        self.f_logging_4.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_log_location = ttk.Label(self.f_logging_1, text="Log Files Location ", width=16)
        self.lbl_log_location.pack(side="left", padx=5)

        self.entry_log_location_value = ttk.Entry(self.f_logging_1, cursor="hand2", width=100)
        self.entry_log_location_value.insert(0, dir_log)
        self.entry_log_location_value.configure(state="readonly")
        self.entry_log_location_value.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_log_location_value.bind("<Button-1>", lambda e: startFile(dir_log))
        self.entry_log_location_value.bind("<Button-3>", lambda e: self.promptDeleteLog())
        CreateToolTip(self.entry_log_location_value, "Location of log file.\n\n- LClick to open the folder.\n- RClick to delete all log files.")

        self.cbtn_verbose = ttk.Checkbutton(self.f_logging_2, text="Verbose logging for whisper", command=lambda: sj.savePartialSetting("verbose", self.cbtn_verbose.instate(["selected"])), style="Switch.TCheckbutton")
        self.cbtn_verbose.pack(side="left", padx=5)

        self.cbtn_keep_log = ttk.Checkbutton(self.f_logging_3, text="Keep log files", command=lambda: sj.savePartialSetting("keep_log", self.cbtn_keep_log.instate(["selected"])), style="Switch.TCheckbutton")
        self.cbtn_keep_log.pack(side="left", padx=5)

        self.lbl_loglevel = ttk.Label(self.f_logging_3, text="— Log level")
        self.lbl_loglevel.pack(side="left", padx=(0, 5))

        self.cb_log_level = ttk.Combobox(self.f_logging_3, values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], state="readonly")
        self.cb_log_level.pack(side="left", padx=0)

        self.cbtn_debug_realtime_record = ttk.Checkbutton(
            self.f_logging_4, text="Debug realtime record", command=lambda: sj.savePartialSetting("debug_realtime_record", self.cbtn_debug_realtime_record.instate(["selected"])), style="Switch.TCheckbutton"
        )
        self.cbtn_debug_realtime_record.pack(side="left", padx=5, pady=(0, 5))

        self.cbtn_debug_translate = ttk.Checkbutton(
            self.f_logging_4, text="Debug translate", command=lambda: sj.savePartialSetting("debug_translate", self.cbtn_debug_translate.instate(["selected"])), style="Switch.TCheckbutton"
        )
        self.cbtn_debug_translate.pack(side="left", padx=5, pady=(0, 5))

        # model
        self.ft1lf_model = tk.LabelFrame(self.ft_general, text="• Model")
        self.ft1lf_model.pack(side="top", fill="x", padx=5, pady=5)

        # label model location
        self.f_model_1 = ttk.Frame(self.ft1lf_model)
        self.f_model_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_model_2 = ttk.Frame(self.ft1lf_model)
        self.f_model_2.pack(side="top", fill="x", padx=5)

        self.f_model_3 = ttk.Frame(self.ft1lf_model)
        self.f_model_3.pack(side="top", fill="x", padx=5)

        self.lbl_model_location = ttk.Label(self.f_model_1, text="Model Location ", width=16)
        self.lbl_model_location.pack(side="left", padx=5)

        self.entry_model_location_value = ttk.Entry(self.f_model_1, cursor="hand2", width=100)
        self.entry_model_location_value.insert(0, get_default_download_root())
        self.entry_model_location_value.configure(state="readonly")
        self.entry_model_location_value.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_model_location_value.bind("<Button-1>", lambda e: startFile(get_default_download_root()))
        CreateToolTip(self.entry_model_location_value, "Location of the model file.\n\n- LClick to open the folder")

        # small
        self.lf_md_dl1 = ttk.Frame(self.f_model_2)
        self.lf_md_dl1.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_tiny = ttk.LabelFrame(self.lf_md_dl1, text="Tiny")
        self.lf_model_tiny.pack(side="left")

        self.btn_interact_tiny = ttk.Button(self.lf_model_tiny, text="Verify", command=lambda: self.model_check("tiny", self.btn_interact_tiny))
        self.btn_interact_tiny.pack(side="left", padx=5)

        # small en
        self.lf_md_dl2 = ttk.Frame(self.f_model_2)
        self.lf_md_dl2.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_tiny_eng = ttk.LabelFrame(self.lf_md_dl2, text="Tiny (en)")
        self.lf_model_tiny_eng.pack(side="left")

        self.btn_interact_tiny_eng = ttk.Button(self.lf_model_tiny_eng, text="Verify", command=lambda: self.model_check("tiny.en", self.btn_interact_tiny_eng))
        self.btn_interact_tiny_eng.pack(side="left", padx=5)

        # base
        self.lf_md_dl3 = ttk.Frame(self.f_model_2)
        self.lf_md_dl3.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_base = ttk.LabelFrame(self.lf_md_dl3, text="Base")
        self.lf_model_base.pack(side="left")

        self.btn_interact_base = ttk.Button(self.lf_model_base, text="Verify", command=lambda: self.model_check("base", self.btn_interact_base))
        self.btn_interact_base.pack(side="left", padx=5)

        # base en
        self.lf_md_dl4 = ttk.Frame(self.f_model_2)
        self.lf_md_dl4.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_base_eng = ttk.LabelFrame(self.lf_md_dl4, text="Base (en)")
        self.lf_model_base_eng.pack(side="left")

        self.btn_interact_base_eng = ttk.Button(self.lf_model_base_eng, text="Verify", command=lambda: self.model_check("base.en", self.btn_interact_base_eng))
        self.btn_interact_base_eng.pack(side="left", padx=5)

        # small
        self.lf_md_dl5 = ttk.Frame(self.f_model_2)
        self.lf_md_dl5.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_small = ttk.LabelFrame(self.lf_md_dl5, text="Small")
        self.lf_model_small.pack(side="left")

        self.btn_interact_small = ttk.Button(self.lf_model_small, text="Verify", command=lambda: self.model_check("small", self.btn_interact_small))
        self.btn_interact_small.pack(side="left", padx=5)

        # small en
        self.lf_md_dl6 = ttk.Frame(self.f_model_2)
        self.lf_md_dl6.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_small_eng = ttk.LabelFrame(self.lf_md_dl6, text="Small (en)")
        self.lf_model_small_eng.pack(side="left")

        self.btn_interact_small_eng = ttk.Button(self.lf_model_small_eng, text="Verify", command=lambda: self.model_check("small.en", self.btn_interact_small_eng))
        self.btn_interact_small_eng.pack(side="left", padx=5)

        # medium
        self.lf_md_dl7 = ttk.Frame(self.f_model_2)
        self.lf_md_dl7.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_medium = ttk.LabelFrame(self.lf_md_dl7, text="Medium")
        self.lf_model_medium.pack(side="left")

        self.btn_interact_medium = ttk.Button(self.lf_model_medium, text="Verify", command=lambda: self.model_check("medium", self.btn_interact_medium))
        self.btn_interact_medium.pack(side="left", padx=5)

        # medium en
        self.lf_md_dl8 = ttk.Frame(self.f_model_2)
        self.lf_md_dl8.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_medium_eng = ttk.LabelFrame(self.lf_md_dl8, text="Medium (en)")
        self.lf_model_medium_eng.pack(side="left")

        self.btn_interact_medium_eng = ttk.Button(self.lf_model_medium_eng, text="Verify", command=lambda: self.model_check("medium.en", self.btn_interact_medium_eng))
        self.btn_interact_medium_eng.pack(side="left", padx=5)

        # large v1
        self.lf_md_dl9 = ttk.Frame(self.f_model_2)
        self.lf_md_dl9.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_large_v1 = ttk.LabelFrame(self.lf_md_dl9, text="Large (v1)")
        self.lf_model_large_v1.pack(side="left")

        self.btn_interact_large_v1 = ttk.Button(self.lf_model_large_v1, text="Verify", command=lambda: self.model_check("large-v1", self.btn_interact_large_v1))
        self.btn_interact_large_v1.pack(side="left", padx=5)

        # large v2
        self.lf_md_dl10 = ttk.Frame(self.f_model_2)
        self.lf_md_dl10.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_large_v2 = ttk.LabelFrame(self.lf_md_dl10, text="Large (v2)")
        self.lf_model_large_v2.pack(side="left")

        self.btn_interact_large_v2 = ttk.Button(self.lf_model_large_v2, text="Verify", command=lambda: self.model_check("large-v2", self.btn_interact_large_v2))
        self.btn_interact_large_v2.pack(side="left", padx=5)

        # ------------------ Transcribe  ------------------
        self.lf_tc_result = tk.LabelFrame(self.ft_transcribe, text="• Result")
        self.lf_tc_result.pack(side="top", fill="x", padx=5, pady=5)

        self.f_tc_result_1 = ttk.Frame(self.lf_tc_result)
        self.f_tc_result_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_tc_result_2 = ttk.Frame(self.lf_tc_result)
        self.f_tc_result_2.pack(side="top", fill="x", pady=5, padx=5)

        self.lf_tc_params = tk.LabelFrame(self.ft_transcribe, text="• Input Parameters")
        self.lf_tc_params.pack(side="top", fill="x", padx=5, pady=5)

        self.f_tc_params_1 = ttk.Frame(self.lf_tc_params)
        self.f_tc_params_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_tc_params_2 = ttk.Frame(self.lf_tc_params)
        self.f_tc_params_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_tc_params_3 = ttk.Frame(self.lf_tc_params)
        self.f_tc_params_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_tc_params_4 = ttk.Frame(self.lf_tc_params)
        self.f_tc_params_4.pack(side="top", fill="x", pady=5, padx=5)

        self.f_tc_params_5 = ttk.Frame(self.lf_tc_params)
        self.f_tc_params_5.pack(side="top", fill="x", pady=5, padx=5)

        # Result
        self.lbl_separate_text_with = ttk.Label(self.f_tc_result_1, text="Text Separator", width=18)
        self.lbl_separate_text_with.pack(side="left", padx=5)
        CreateToolTip(self.lbl_separate_text_with, "Set the separator for text that is transcribed or translated.\n\nDefault value \\n", wrapLength=400)

        self.entry_separate_text_with = ttk.Entry(self.f_tc_result_1)
        self.entry_separate_text_with.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_separate_text_with.bind("<KeyRelease>", lambda e: sj.savePartialSetting("separate_with", self.entry_separate_text_with.get()))
        CreateToolTip(self.entry_separate_text_with, "Set the separator for text that is transcribed or translated.\n\nDefault value \\n", wrapLength=400)

        self.lbl_max_temp = ttk.Label(self.f_tc_result_2, text="Max Sentences", width=18)
        self.lbl_max_temp.pack(side="left", padx=5)
        CreateToolTip(
            self.lbl_max_temp,
            "Set max number of sentences kept between each buffer reset.\n\nOne sentence equals one max buffer. So if max buffer is 30 seconds, the words that are in those 30 seconds is the sentence.\n\nDefault value is 5.",
        )

        self.spn_max_sentences = ttk.Spinbox(
            self.f_tc_result_2, from_=1, to=30, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: sj.savePartialSetting("max_sentences", int(self.spn_max_sentences.get()))
        )
        self.spn_max_sentences.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_max_sentences, 1, 30, lambda: sj.savePartialSetting("max_sentences", int(self.spn_max_sentences.get()))))
        self.spn_max_sentences.pack(side="left", padx=5)
        CreateToolTip(
            self.spn_max_sentences,
            "Set max number of sentences kept between each buffer reset.\n\nOne sentence equals one max buffer. So if max buffer is 30 seconds, the words that are in those 30 seconds is the sentence.\n\nDefault value is 5.",
        )

        self.lbl_max_temp = ttk.Label(self.f_tc_result_2, text="Max Temp Files", width=18)
        self.lbl_max_temp.pack(side="left", padx=5)
        CreateToolTip(self.lbl_max_temp, "Set max number of temporary files kept when recording from device that is not mono.\n\nDefault value is 200.")

        self.spn_max_temp = ttk.Spinbox(
            self.f_tc_result_2, from_=50, to=1000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: sj.savePartialSetting("max_temp", int(self.spn_max_temp.get()))
        )
        self.spn_max_temp.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_max_temp, 50, 1000, lambda: sj.savePartialSetting("max_temp", int(self.spn_max_temp.get()))))
        self.spn_max_temp.pack(side="left", padx=5)
        CreateToolTip(self.spn_max_temp, "Set max number of temporary files kept when recording from device that is not mono.\n\nDefault value is 200.")

        # INPUT param
        self.lbl_sample_rate = ttk.Label(self.f_tc_params_1, text="Sample Rate", width=18)
        self.lbl_sample_rate.pack(side="left", padx=5)
        CreateToolTip(self.lbl_sample_rate, "Set the sample rate for the audio recording. \n\nDefault value is 16000.")

        self.spn_sample_rate = ttk.Spinbox(
            self.f_tc_params_1, from_=8000, to=48000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: sj.savePartialSetting("sample_rate", int(self.spn_sample_rate.get()))
        )
        self.spn_sample_rate.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_sample_rate, 8000, 48000, lambda: sj.savePartialSetting("sample_rate", int(self.spn_sample_rate.get()))))
        self.spn_sample_rate.pack(side="left", padx=5)
        CreateToolTip(self.spn_sample_rate, "Set the sample rate for the audio recording. \n\nDefault value is 16000.")

        self.lbl_chunk_size = ttk.Label(self.f_tc_params_1, text="Chunk Size", width=18)
        self.lbl_chunk_size.pack(side="left", padx=5)
        CreateToolTip(self.lbl_chunk_size, "Set the chunk size for the audio recording. \n\nDefault value is 1024.")

        self.spn_chunk_size = ttk.Spinbox(
            self.f_tc_params_1, from_=512, to=65536, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: sj.savePartialSetting("chunk_size", int(self.spn_chunk_size.get()))
        )
        self.spn_chunk_size.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_chunk_size, 512, 65536, lambda: sj.savePartialSetting("chunk_size", int(self.spn_chunk_size.get()))))
        self.spn_chunk_size.pack(side="left", padx=5)
        CreateToolTip(self.spn_chunk_size, "Set the chunk size for the audio recording. \n\nDefault value is 1024.")

        self.lbl_tc_rate = ttk.Label(self.f_tc_params_1, text="Transcribe Rate (ms)", width=18)
        self.lbl_tc_rate.pack(side="left", padx=5)

        self.spn_tc_rate = ttk.Spinbox(
            self.f_tc_params_1, from_=1, to=1000, validate="key", validatecommand=(self.root.register(self.number_only), "%P"), command=lambda: sj.savePartialSetting("transcribe_rate", int(self.spn_tc_rate.get()))
        )

        self.spn_tc_rate.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_tc_rate, 1, 1000, lambda: sj.savePartialSetting("transcribe_rate", int(self.spn_tc_rate.get()))))
        self.spn_tc_rate.pack(side="left", padx=5)
        createMultipleTooltips([self.spn_tc_rate, self.lbl_tc_rate],  "Set the transcribe rate or the time between each transcribe check. \n\nFor more real time experience you can lower it more. The lower the value, the more resource it will use.\n\nIf you lower the transcribe rate, you should also lower the max buffer for a better experience.\n\nDefault value is 300ms.", wrapLength=350)

        # 2
        self.cbtn_auto_sample_rate = ttk.Checkbutton(
            self.f_tc_params_2, text="Auto sample rate", command=lambda: sj.savePartialSetting("auto_sample_rate", self.cbtn_auto_sample_rate.instate(["selected"])), style="Switch.TCheckbutton"
        )
        self.cbtn_auto_sample_rate.pack(side="left", padx=5)
        CreateToolTip(
            self.cbtn_auto_sample_rate,
            "If checked, the sample rate will be automatically set based on the device default sample rate. \n\nCheck this option if you are having issues.\n\nDefault is false/unchecked\n*Speaker input will always be true for this option.",
            wrapLength=400,
        )

        self.cbtn_auto_channels_amount = ttk.Checkbutton(
            self.f_tc_params_2, text="Auto channels amount", command=lambda: sj.savePartialSetting("auto_channels_amount", self.cbtn_auto_channels_amount.instate(["selected"])), style="Switch.TCheckbutton"
        )
        self.cbtn_auto_channels_amount.pack(side="left", padx=5)
        CreateToolTip(
            self.cbtn_auto_channels_amount,
            "If checked, the channels amount will be automatically set based on the device default channels amount. \n\nCheck this option if you are having issues.\n\nDefault is false/unchecked (channel amount is defaulted to 1 on mic input if value is false)\n*Speaker input will always be true for this option.",
            wrapLength=400,
        )

        self.cbtn_keep_temp = ttk.Checkbutton(
            self.f_tc_params_2, text="Keep temp files", command=lambda: sj.savePartialSetting("keep_temp", self.cbtn_keep_temp.instate(["selected"])), style="Switch.TCheckbutton"
        )
        self.cbtn_keep_temp.pack(side="left", padx=5)
        CreateToolTip(self.cbtn_keep_temp, "If checked, will not delete temporary audio file that might be created by the program. \n\nDefault value is false/unchecked.")

        # ------------------ Buffer ------------------
        self.lf_buffer = ttk.LabelFrame(self.f_tc_params_3, text="Max Buffer (seconds)")
        self.lf_buffer.pack(side="left", padx=5, fill="x", expand=True)

        self.f_buffer_1 = ttk.Frame(self.lf_buffer)
        self.f_buffer_1.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_hint_buffer = ttk.Label(self.f_buffer_1, text="❓")
        self.lbl_hint_buffer.pack(side="right", padx=5)
        CreateToolTip(self.lbl_hint_buffer, "Max buffer is the maximum continous recording time. After it is reached buffer will be reset.\n\nTips: Lower the buffer if your transcribe rate is low for a faster and more accurate result.")

        self.lbl_buffer_mic = ttk.Label(self.f_buffer_1, text="Mic", width=18)
        self.lbl_buffer_mic.pack(side="left", padx=5)
        CreateToolTip(
            self.lbl_buffer_mic,
            "Set the max buffer (in seconds) for microphone input.\n\nThe longer the buffer, the more time it will take to transcribe the audio. Not recommended to have very long buffer on low end PC.\n\nDefault value is 10 seconds.",
        )

        self.spn_buffer_mic = ttk.Spinbox(
            self.f_buffer_1,
            from_=3,
            to=300,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("mic_maxBuffer", int(self.spn_buffer_mic.get())),
        )
        self.spn_buffer_mic.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(self.spn_buffer_mic, 3, 300, lambda: sj.savePartialSetting("mic_maxBuffer", int(self.spn_buffer_mic.get()))),
        )
        self.spn_buffer_mic.pack(side="left", padx=5)
        CreateToolTip(
            self.spn_buffer_mic,
            "Set the max buffer (in seconds) for microphone input.\n\nThe longer the buffer, the more time it will take to transcribe the audio. Not recommended to have very long buffer on low end PC.\n\nDefault value is 10 seconds.",
        )

        if platform.system() == "Windows":
            self.lbl_buffer_speaker = ttk.Label(self.f_buffer_1, text="Speaker", width=18)
            self.lbl_buffer_speaker.pack(side="left", padx=5)
            CreateToolTip(
                self.lbl_buffer_speaker,
                "Set the max buffer (in seconds) for speaker input.\n\nThe longer the buffer, the more time it will take to transcribe the audio. Not recommended to have very long buffer on low end PC.\n\nDefault value is 10 seconds.\n\n*This Setting is only for Windows OS.",
            )

            self.spn_buffer_speaker = ttk.Spinbox(
                self.f_buffer_1,
                from_=3,
                to=300,
                validate="key",
                validatecommand=(self.root.register(self.number_only), "%P"),
                command=lambda: sj.savePartialSetting("speaker_maxBuffer", int(self.spn_buffer_speaker.get())),
            )
            self.spn_buffer_speaker.bind(
                "<KeyRelease>",
                lambda e: self.verifyMaxNumber(self.spn_buffer_speaker, 3, 300, lambda: sj.savePartialSetting("speaker_maxBuffer", int(self.spn_buffer_speaker.get()))),
            )
            self.spn_buffer_speaker.pack(side="left", padx=5)
            CreateToolTip(
                self.spn_buffer_speaker,
                "Set the max buffer (in seconds) for speaker input.\n\nThe longer the buffer, the more time it will take to transcribe the audio. Not recommended to have very long buffer on low end PC.\n\nDefault value is 10 seconds.\n\n*This Setting is only for Windows OS.",
            )

        # ------------------ Threshold ------------------
        self.lf_threshold = ttk.LabelFrame(self.f_tc_params_4, text="Sound Input Threshold")
        self.lf_threshold.pack(side="left", padx=5, fill="x", expand=True)

        self.f_threshold_1 = ttk.Frame(self.lf_threshold)
        self.f_threshold_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_threshold_2 = ttk.Frame(self.lf_threshold)
        self.f_threshold_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_threshold_3 = ttk.Frame(self.lf_threshold)
        self.f_threshold_3.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_hint_threshold = ttk.Label(self.f_threshold_1, text="❓")
        self.lbl_hint_threshold.pack(side="right", padx=5)
        CreateToolTip(self.lbl_hint_threshold, "Minimum threshold is the minimum volume level that is needed for the audio to be recorded. If set correctly might help to reduce background noise.")

        self.cbtn_enable_threshold = ttk.Checkbutton(
            self.f_threshold_1, text="Enable", command=lambda: sj.savePartialSetting("enable_threshold", self.cbtn_enable_threshold.instate(["selected"])), style="Switch.TCheckbutton"
        )
        self.cbtn_enable_threshold.pack(side="left", padx=5, pady=2)

        self.cbtn_debug_energy = ttk.Checkbutton(
            self.f_threshold_1, text="Log volume level", command=lambda: sj.savePartialSetting("debug_energy", self.cbtn_debug_energy.instate(["selected"])), style="Switch.TCheckbutton"
        )
        self.cbtn_debug_energy.pack(side="left", padx=5, pady=2)
        CreateToolTip(
            self.cbtn_debug_energy,
            "Log the volume level get from recording device. This is useful for setting the threshold value. You can see the logging in terminal. You should turn this off after optimal value is set.\n\n*Might cause performance issue",
            wrapLength=500,
        )

        self.lbl_threshold_mic = ttk.Label(self.f_threshold_2, text="Mic", width=18)
        self.lbl_threshold_mic.pack(side="left", padx=5)

        self.spn_threshold_mic = ttk.Spinbox(
            self.f_threshold_2,
            from_=0,
            to=100000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("mic_energy_threshold", int(self.spn_threshold_mic.get())),
        )
        self.spn_threshold_mic.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(self.spn_threshold_mic, 0, 100000, lambda: sj.savePartialSetting("mic_energy_threshold", int(self.spn_threshold_mic.get()))),
        )
        self.spn_threshold_mic.pack(side="left", padx=5)

        self.btn_auto_mic_threshold = ttk.Button(self.f_threshold_2, text="Auto calculate", command=lambda: self.micAutoThreshold())
        self.btn_auto_mic_threshold.pack(side="left", padx=5)
        CreateToolTip(self.btn_auto_mic_threshold, "Try to auto calculate the mic threshold value. \n\n*Might not be accurate.")

        if platform.system() == "Windows":
            self.lbl_threshold_speaker = ttk.Label(self.f_threshold_3, text="Speaker", width=18)
            self.lbl_threshold_speaker.pack(side="left", padx=5)

            self.spn_threshold_speaker = ttk.Spinbox(
                self.f_threshold_3,
                from_=0,
                to=100000,
                validate="key",
                validatecommand=(self.root.register(self.number_only), "%P"),
                command=lambda: sj.savePartialSetting("speaker_energy_threshold", int(self.spn_threshold_speaker.get())),
            )
            self.spn_threshold_speaker.bind(
                "<KeyRelease>",
                lambda e: self.verifyMaxNumber(self.spn_threshold_speaker, 0, 100000, lambda: sj.savePartialSetting("speaker_energy_threshold", int(self.spn_threshold_speaker.get()))),
            )
            self.spn_threshold_speaker.pack(side="left", padx=5)

            self.btn_auto_speaker_threshold = ttk.Button(self.f_threshold_3, text="Auto calculate", command=lambda: self.speakerAutoThreshold())
            self.btn_auto_speaker_threshold.pack(side="left", padx=5)
            CreateToolTip(self.btn_auto_speaker_threshold, "Try to auto calculate the speaker threshold value. \n\n*Might not be accurate.")

        # whisper args
        self.lf_extra_whisper_args = ttk.LabelFrame(self.f_tc_params_5, text="Whisper Args")
        self.lf_extra_whisper_args.pack(side="left", padx=5, fill="x", expand=True)

        self.f_extra_whisper_args_1 = ttk.Frame(self.lf_extra_whisper_args)
        self.f_extra_whisper_args_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_extra_whisper_args_2 = ttk.Frame(self.lf_extra_whisper_args)
        self.f_extra_whisper_args_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_extra_whisper_args_3 = ttk.Frame(self.lf_extra_whisper_args)
        self.f_extra_whisper_args_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_extra_whisper_args_4 = ttk.Frame(self.lf_extra_whisper_args)
        self.f_extra_whisper_args_4.pack(side="top", fill="x", pady=5, padx=5)

        self.cbtn_condition_on_previous_text = ttk.Checkbutton(
            self.f_extra_whisper_args_1,
            text="Condition on previous text",
            command=lambda: sj.savePartialSetting("condition_on_previous_text", self.cbtn_condition_on_previous_text.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_condition_on_previous_text.pack(side="left", padx=5)
        CreateToolTip(
            self.cbtn_condition_on_previous_text,
            """if True, the previous output of the model is provided as a prompt for the next window;
        \rDisabling may make the text inconsistent across windows, but the model becomes less prone to getting stuck in a failure loop, such as repetition looping or timestamps going out of sync.
        \rDefault value is true/checked""",
        )

        self.lbl_compression_ratio_threshold = ttk.Label(self.f_extra_whisper_args_2, text="Compression threshold", width=18)
        self.lbl_compression_ratio_threshold.pack(side="left", padx=5)

        self.spn_compression_ratio_threshold = ttk.Spinbox(
            self.f_extra_whisper_args_2,
            format="%.2f",
            from_=-100,
            to=100,
            increment=0.1,
            validate="key",
            validatecommand=(self.root.register(self.number_only_float), "%P"),
            command=lambda: sj.savePartialSetting("compression_ratio_threshold", float(self.spn_compression_ratio_threshold.get())),
        )
        self.spn_compression_ratio_threshold.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber_float(self.spn_compression_ratio_threshold, -100, 100, lambda: sj.savePartialSetting("compression_ratio_threshold", float(self.spn_compression_ratio_threshold.get()))),
        )
        self.spn_compression_ratio_threshold.pack(side="left", padx=5)
        createMultipleTooltips(
            [self.lbl_compression_ratio_threshold, self.spn_compression_ratio_threshold], "Compression ratio threshold.\n\nIf the gzip compression ratio is above this value, treat as failed.\n\nDefault value is 2.4"
        )

        self.lbl_logprob_threshold = ttk.Label(self.f_extra_whisper_args_2, text="Logprob threshold", width=18)
        self.lbl_logprob_threshold.pack(side="left", padx=5)

        self.spn_logprob_threshold = ttk.Spinbox(
            self.f_extra_whisper_args_2,
            format="%.2f",
            from_=-100,
            to=100,
            increment=0.1,
            validate="key",
            validatecommand=(self.root.register(self.number_only_float), "%P"),
            command=lambda: sj.savePartialSetting("logprob_threshold", float(self.spn_logprob_threshold.get())),
        )
        self.spn_logprob_threshold.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber_float(self.spn_logprob_threshold, -100, 100, lambda: sj.savePartialSetting("logprob_threshold", float(self.spn_logprob_threshold.get()))),
        )
        self.spn_logprob_threshold.pack(side="left", padx=5)
        createMultipleTooltips([self.lbl_logprob_threshold, self.spn_logprob_threshold], "If the average log probability over sampled tokens is below this value, treat as failed.\n\nDefault value is -1.0")

        self.lbl_no_speech_threshold = ttk.Label(self.f_extra_whisper_args_2, text="No speech threshold", width=18)
        self.lbl_no_speech_threshold.pack(side="left", padx=5)

        self.spn_no_speech_threshold = ttk.Spinbox(
            self.f_extra_whisper_args_2,
            format="%.2f",
            from_=-100,
            to=100,
            increment=0.1,
            validatecommand=(self.root.register(self.number_only_float), "%P"),
            command=lambda: sj.savePartialSetting("no_speech_threshold", float(self.spn_no_speech_threshold.get())),
        )
        self.spn_no_speech_threshold.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber_float(self.spn_no_speech_threshold, -100, 100, lambda: sj.savePartialSetting("no_speech_threshold", float(self.spn_no_speech_threshold.get()))),
        )
        self.spn_no_speech_threshold.pack(side="left", padx=5)
        createMultipleTooltips(
            [self.lbl_no_speech_threshold, self.spn_no_speech_threshold],
            """If the no_speech probability is higher than this value AND the average log probability
        \rover sampled tokens is below `logprob_threshold`, consider the segment as silent.\n\nDefault value is 0.6""",
        )

        self.lbl_initial_prompt = ttk.Label(self.f_extra_whisper_args_3, text="Initial prompt", width=18)
        self.lbl_initial_prompt.pack(side="left", padx=5)

        self.entry_initial_prompt = ttk.Entry(self.f_extra_whisper_args_3)
        self.entry_initial_prompt.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_initial_prompt.bind("<KeyRelease>", lambda e: sj.savePartialSetting("initial_prompt", self.entry_initial_prompt.get()))
        createMultipleTooltips([self.lbl_initial_prompt, self.entry_initial_prompt], "optional text to provide as a prompt for the first window.\n\nDefault is empty")

        self.lbl_temperature = ttk.Label(self.f_extra_whisper_args_3, text="Temperature", width=18)
        self.lbl_temperature.pack(side="left", padx=5)

        self.entry_temperature = ttk.Entry(self.f_extra_whisper_args_3)
        self.entry_temperature.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_temperature.bind("<KeyRelease>", lambda e: sj.savePartialSetting("temperature", self.entry_temperature.get()))
        createMultipleTooltips(
            [self.lbl_temperature, self.entry_temperature],
            "Temperature for sampling. It can be a tuple of temperatures, which will be successively used upon failures according to either `compression_ratio_threshold` or `logprob_threshold`.\n\nDefault is 0.0, 0.2, 0.4, 0.6, 0.8, 1.0",
        )

        self.btn_verify_temperature = ttk.Button(self.f_extra_whisper_args_3, text="Verify", command=lambda: self.verifyTemp())
        self.btn_verify_temperature.pack(side="left", padx=5)
        CreateToolTip(self.btn_verify_temperature, "Verify temperature input.")

        rng = random.randint(0, 10000)
        self.lbl_extra_whisper_args = ttk.Label(self.f_extra_whisper_args_4, text="Extra whisper args", width=18, cursor="hand2")
        self.lbl_extra_whisper_args.pack(side="left", padx=5)
        self.lbl_extra_whisper_args.bind("<Button-1>", lambda e: MBoxText(rng, self.root, "Whisper Args", hint))
        CreateToolTip(self.lbl_extra_whisper_args, "Click to see the available arguments.")

        self.entry_whisper_extra_args = ttk.Entry(self.f_extra_whisper_args_4)
        self.entry_whisper_extra_args.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_whisper_extra_args.bind("<KeyRelease>", lambda e: sj.savePartialSetting("whisper_extra_args", self.entry_whisper_extra_args.get()))
        CreateToolTip(self.entry_whisper_extra_args, "Whisper extra arguments.\n\nDefault is empty")

        hint = (
            "Extra arguments to pass to the whisper command. Default value is empty / using whisper default\n(Usage value shown as example here are only for reference)"
            #
            f"\n\n# Maximum number of tokens to sample"
            f"\nsample_len: int\n--sample_len 0"
            #
            f"\n\n# Number of independent samples to collect, when t > 0"
            f"\nbest_of: int\n--best_of 0"
            #
            f"\n\n# Number of beams in beam search, when t == 0"
            f"\nbeam_size: int\n--beam_size 0"
            #
            f"\n\n# Patience in beam search (https://arxiv.org/abs/2204.05424)"
            f"\npatience: float\n--patience 0.0"
            #
            f"\n\n# Options for ranking generations (either beams or best-of-N samples)"
            f"\n# 'alpha' in Google NMT, None defaults to length norm"
            f"\nlength_penalty: float = None\n--length_penalty 0.0"
            #
            f"\n\n# Text or tokens for the previous context"
            f'\nprompt: str or [int]\n--prompt "hello world" or --prompt [1, 2, 3]'
            #
            f"\n\n# Text or tokens to prefix the current context"
            f'\nprefix: str or [int]\n--prefix "hello world" or --prefix [1, 2, 3]'
            #
            f"\n\n# Text or tokens for the previous context"
            f"\nsuppress_blank: bool\n--suppress_blank true"
            #
            f'\n\n# List of tokens ids (or comma-separated token ids) to suppress\n# "-1" will suppress a set of symbols as defined in `tokenizer.non_speech_tokens()`'
            f'\nsuppress_tokens: str or [int]\n--suppress_tokens "-1" or --suppress_tokens [-1, 0]'
            #
            f"\n\n# Timestamp sampling options"
            f"\nwithout_timestamps: bool\n--without_timestamps true"
            #
            f"\n\n# The initial timestamp cannot be later than this"
            f"\nmax_initial_timestamp: float\n--max_initial_timestamp 1.0"
            #
            f"\n\n# Implementation details"
            f"\n# Use fp16 for most of the calculation"
            f"\nfp16: bool\n--fp16 true"
        )
        CreateToolTipOnText(self.entry_whisper_extra_args, hint, geometry="700x250")

        self.btn_verify = ttk.Button(self.f_extra_whisper_args_4, text="Verify", command=lambda: self.verifyWhisperArgs())
        self.btn_verify.pack(side="left", padx=5)
        CreateToolTip(self.btn_verify, "Verify the extra arguments.")

        # ------------------ Translate ------------------
        # translate
        self.lf_libre = tk.LabelFrame(self.ft_translate, text="• Libre Translate Setting")
        self.lf_libre.pack(side="top", fill="x", padx=5, pady=5)

        self.f_libre_1 = ttk.Frame(self.lf_libre)
        self.f_libre_1.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_libre_key = ttk.Label(self.f_libre_1, text="API Key")
        self.lbl_libre_key.pack(side="left", padx=5, pady=5)

        self.entry_libre_key = ttk.Entry(self.f_libre_1)
        self.entry_libre_key.pack(side="left", padx=5, pady=5)
        self.entry_libre_key.bind("<KeyRelease>", lambda e: sj.savePartialSetting("libre_api_key", self.entry_libre_key.get()))
        createMultipleTooltips([self.lbl_libre_key, self.entry_libre_key], "Libre Translate API Key. Leave empty if not needed or host locally.")

        self.lbl_libre_host = ttk.Label(self.f_libre_1, text="Host")
        self.lbl_libre_host.pack(side="left", padx=5, pady=5)

        self.entry_libre_host = ttk.Entry(self.f_libre_1, width=40)
        self.entry_libre_host.pack(side="left", padx=5, pady=5)
        self.entry_libre_host.bind("<KeyRelease>", lambda e: sj.savePartialSetting("libre_host", self.entry_libre_host.get()))
        createMultipleTooltips(
            [self.lbl_libre_host, self.entry_libre_host],
            "The host of Libre Translate. You can check out the official instance/mirrors at https://github.com/LibreTranslate/LibreTranslate or host your own instance",
            wrapLength=300,
        )

        self.lbl_libre_port = ttk.Label(self.f_libre_1, text="Port")
        self.lbl_libre_port.pack(side="left", padx=5, pady=5)
        self.lbl_libre_port.bind("<KeyRelease>", lambda e: sj.savePartialSetting("libre_port", self.entry_libre_port.get()))

        self.entry_libre_port = ttk.Entry(self.f_libre_1)
        self.entry_libre_port.pack(side="left", padx=5, pady=5)
        self.entry_libre_port.bind("<KeyRelease>", lambda e: sj.savePartialSetting("libre_port", self.entry_libre_port.get()))
        createMultipleTooltips([self.lbl_libre_port, self.entry_libre_port], "Libre Translate Port.")

        self.cbtn_libre_https = ttk.Checkbutton(self.f_libre_1, text="Use HTTPS", command=lambda: sj.savePartialSetting("libre_https", self.cbtn_libre_https.instate(["selected"])), style="Switch.TCheckbutton")
        self.cbtn_libre_https.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.cbtn_libre_https, "Set it to false if you're hosting locally.")

        # ------------------ Textbox ------------------
        self.f_textbox = ttk.Frame(self.ft_textbox)
        self.f_textbox.pack(side="top", fill="both", padx=5, pady=5, expand=False)

        # mw tc
        self.lf_mw_tc = tk.LabelFrame(self.f_textbox, text="• Main Window Transcribed Speech")
        self.lf_mw_tc.pack(side="top", padx=5, pady=5, fill="x", expand=True)

        self.lbl_mw_tc_max = ttk.Label(self.lf_mw_tc, text="Max Length")
        self.lbl_mw_tc_max.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.lbl_mw_tc_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.spn_mw_tc_max = ttk.Spinbox(
            self.lf_mw_tc,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("tb_mw_tc_max", int(self.spn_mw_tc_max.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_mw_tc_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_mw_tc_max, 0, 5000, lambda: sj.savePartialSetting("tb_mw_tc_max", int(self.spn_mw_tc_max.get()))) or self.preview_changes_tb())
        self.spn_mw_tc_max.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.spn_mw_tc_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.lbl_mw_tc_font = ttk.Label(self.lf_mw_tc, text="Font")
        self.lbl_mw_tc_font.pack(side="left", padx=5, pady=5)

        self.cb_mw_tc_font = ttk.Combobox(self.lf_mw_tc, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tc_font.pack(side="left", padx=5, pady=5)
        self.cb_mw_tc_font.bind("<<ComboboxSelected>>", lambda e: sj.savePartialSetting("tb_mw_tc_font", self.cb_mw_tc_font.get()) or self.preview_changes_tb())

        self.lbl_mw_tc_font_size = ttk.Label(self.lf_mw_tc, text="Font Size")
        self.lbl_mw_tc_font_size.pack(side="left", padx=5, pady=5)

        self.spn_mw_tc_font_size = ttk.Spinbox(
            self.lf_mw_tc,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("tb_mw_tc_font_size", int(self.spn_mw_tc_font_size.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_mw_tc_font_size.bind(
            "<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_mw_tc_font_size, 3, 120, lambda: sj.savePartialSetting("tb_mw_tc_font_size", int(self.spn_mw_tc_font_size.get()))) or self.preview_changes_tb()
        )
        self.spn_mw_tc_font_size.pack(side="left", padx=5, pady=5)

        self.cbtn_mw_tc_font_bold = ttk.Checkbutton(
            self.lf_mw_tc, text="Bold", command=lambda: sj.savePartialSetting("tb_mw_tc_font_bold", self.cbtn_mw_tc_font_bold.instate(["selected"])) or self.preview_changes_tb()
        )
        self.cbtn_mw_tc_font_bold.pack(side="left", padx=5, pady=5)

        # mw tl
        self.lf_mw_tl = tk.LabelFrame(self.f_textbox, text="• Main Window Translated Speech")
        self.lf_mw_tl.pack(side="top", padx=5, pady=5, fill="x", expand=True)

        self.lbl_mw_tl_max = ttk.Label(self.lf_mw_tl, text="Max Length")
        self.lbl_mw_tl_max.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.lbl_mw_tl_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.spn_mw_tl_max = ttk.Spinbox(
            self.lf_mw_tl,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("tb_mw_tl_max", int(self.spn_mw_tl_max.get()) or self.preview_changes_tb()),
            width=10,
        )
        self.spn_mw_tl_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_mw_tl_max, 0, 5000, lambda: sj.savePartialSetting("tb_mw_tl_max", int(self.spn_mw_tl_max.get())) or self.preview_changes_tb()))
        self.spn_mw_tl_max.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.spn_mw_tl_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.lbl_mw_tl_font = ttk.Label(self.lf_mw_tl, text="Font")
        self.lbl_mw_tl_font.pack(side="left", padx=5, pady=5)

        self.cb_mw_tl_font = ttk.Combobox(self.lf_mw_tl, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tl_font.pack(side="left", padx=5, pady=5)
        self.cb_mw_tl_font.bind("<<ComboboxSelected>>", lambda e: sj.savePartialSetting("tb_mw_tl_font", self.cb_mw_tl_font.get()) or self.preview_changes_tb())

        self.lbl_mw_tl_font_size = ttk.Label(self.lf_mw_tl, text="Font Size")
        self.lbl_mw_tl_font_size.pack(side="left", padx=5, pady=5)

        self.spn_mw_tl_font_size = ttk.Spinbox(
            self.lf_mw_tl,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("tb_mw_tl_font_size", int(self.spn_mw_tl_font_size.get()) or self.preview_changes_tb()),
            width=10,
        )
        self.spn_mw_tl_font_size.bind(
            "<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_mw_tl_font_size, 3, 120, lambda: sj.savePartialSetting("tb_mw_tl_font_size", int(self.spn_mw_tl_font_size.get())) or self.preview_changes_tb())
        )
        self.spn_mw_tl_font_size.pack(side="left", padx=5, pady=5)

        self.cbtn_mw_tl_font_bold = ttk.Checkbutton(
            self.lf_mw_tl, text="Bold", command=lambda: sj.savePartialSetting("tb_mw_tl_font_bold", self.cbtn_mw_tl_font_bold.instate(["selected"])) or self.preview_changes_tb()
        )
        self.cbtn_mw_tl_font_bold.pack(side="left", padx=5, pady=5)

        # detached tc
        self.lf_ex_tc = tk.LabelFrame(self.f_textbox, text="• Subtitle Window Transcribed Speech")
        self.lf_ex_tc.pack(side="top", padx=5, pady=5, fill="x", expand=True)

        self.lbl_ex_tc_max = ttk.Label(self.lf_ex_tc, text="Max Length")
        self.lbl_ex_tc_max.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.lbl_ex_tc_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.spn_ex_tc_max = ttk.Spinbox(
            self.lf_ex_tc,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("tb_ex_tc_max", int(self.spn_ex_tc_max.get()) or self.preview_changes_tb()),
            width=10,
        )
        self.spn_ex_tc_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_ex_tc_max, 0, 5000, lambda: sj.savePartialSetting("tb_ex_tc_max", int(self.spn_ex_tc_max.get())) or self.preview_changes_tb()))
        self.spn_ex_tc_max.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.spn_ex_tc_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.lbl_ex_tc_font = ttk.Label(self.lf_ex_tc, text="Font")
        self.lbl_ex_tc_font.pack(side="left", padx=5, pady=5)

        self.cb_ex_tc_font = ttk.Combobox(self.lf_ex_tc, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tc_font.pack(side="left", padx=5, pady=5)
        self.cb_ex_tc_font.bind("<<ComboboxSelected>>", lambda e: sj.savePartialSetting("tb_ex_tc_font", self.cb_ex_tc_font.get()) or self.preview_changes_tb())

        self.lbl_ex_tc_font_size = ttk.Label(self.lf_ex_tc, text="Font Size")
        self.lbl_ex_tc_font_size.pack(side="left", padx=5, pady=5)

        self.spn_ex_tc_font_size = ttk.Spinbox(
            self.lf_ex_tc,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("tb_ex_tc_font_size", int(self.spn_ex_tc_font_size.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_ex_tc_font_size.bind(
            "<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_ex_tc_font_size, 3, 120, lambda: sj.savePartialSetting("tb_ex_tc_font_size", int(self.spn_ex_tc_font_size.get())) or self.preview_changes_tb())
        )
        self.spn_ex_tc_font_size.pack(side="left", padx=5, pady=5)

        self.cbtn_ex_tc_font_bold = ttk.Checkbutton(
            self.lf_ex_tc, text="Bold", command=lambda: sj.savePartialSetting("tb_ex_tc_font_bold", self.cbtn_ex_tc_font_bold.instate(["selected"])) or self.preview_changes_tb()
        )
        self.cbtn_ex_tc_font_bold.pack(side="left", padx=5, pady=5)

        self.lbl_ex_tc_font_color = ttk.Label(self.lf_ex_tc, text="Font Color")
        self.lbl_ex_tc_font_color.pack(side="left", padx=5, pady=5)

        self.entry_ex_tc_font_color = ttk.Entry(self.lf_ex_tc, width=10)
        self.entry_ex_tc_font_color.pack(side="left", padx=5, pady=5)
        self.entry_ex_tc_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_font_color, self.entry_ex_tc_font_color.get(), self.root)
            or sj.savePartialSetting("tb_ex_tc_font_color", self.entry_ex_tc_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tc_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tc_bg_color = ttk.Label(self.lf_ex_tc, text="Background Color")
        self.lbl_ex_tc_bg_color.pack(side="left", padx=5, pady=5)

        self.entry_ex_tc_bg_color = ttk.Entry(self.lf_ex_tc, width=10)
        self.entry_ex_tc_bg_color.pack(side="left", padx=5, pady=5)
        self.entry_ex_tc_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_bg_color, self.entry_ex_tc_bg_color.get(), self.root) or sj.savePartialSetting("tb_ex_tc_bg_color", self.entry_ex_tc_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tc_bg_color.bind("<Key>", lambda e: "break")

        # detached tl
        self.lf_ex_tl = tk.LabelFrame(self.f_textbox, text="• Subtitle Window Translated Speech")
        self.lf_ex_tl.pack(side="top", padx=5, pady=5, fill="x", expand=True)

        self.lbl_ex_tl_max = ttk.Label(self.lf_ex_tl, text="Max Length")
        self.lbl_ex_tl_max.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.lbl_ex_tl_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.spn_ex_tl_max = ttk.Spinbox(
            self.lf_ex_tl,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("tb_ex_tl_max", int(self.spn_ex_tl_max.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_ex_tl_max.bind("<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_ex_tl_max, 0, 5000, lambda: sj.savePartialSetting("tb_ex_tl_max", int(self.spn_ex_tl_max.get())) or self.preview_changes_tb()))
        self.spn_ex_tl_max.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.spn_ex_tl_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.lbl_ex_tl_font = ttk.Label(self.lf_ex_tl, text="Font")
        self.lbl_ex_tl_font.pack(side="left", padx=5, pady=5)

        self.cb_ex_tl_font = ttk.Combobox(self.lf_ex_tl, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tl_font.pack(side="left", padx=5, pady=5)
        self.cb_ex_tl_font.bind("<<ComboboxSelected>>", lambda e: sj.savePartialSetting("tb_ex_tl_font", self.cb_ex_tl_font.get()) or self.preview_changes_tb())

        self.lbl_ex_tl_font_size = ttk.Label(self.lf_ex_tl, text="Font Size")
        self.lbl_ex_tl_font_size.pack(side="left", padx=5, pady=5)

        self.spn_ex_tl_font_size = ttk.Spinbox(
            self.lf_ex_tl,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.savePartialSetting("tb_ex_tl_font_size", int(self.spn_ex_tl_font_size.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_ex_tl_font_size.bind(
            "<KeyRelease>", lambda e: self.verifyMaxNumber(self.spn_ex_tl_font_size, 3, 120, lambda: sj.savePartialSetting("tb_ex_tl_font_size", int(self.spn_ex_tl_font_size.get())) or self.preview_changes_tb())
        )
        self.spn_ex_tl_font_size.pack(side="left", padx=5, pady=5)

        self.cbtn_ex_tl_font_bold = ttk.Checkbutton(
            self.lf_ex_tl, text="Bold", command=lambda: sj.savePartialSetting("tb_ex_tl_font_bold", self.cbtn_ex_tl_font_bold.instate(["selected"])) or self.preview_changes_tb()
        )
        self.cbtn_ex_tl_font_bold.pack(side="left", padx=5, pady=5)

        self.lbl_ex_tl_font_color = ttk.Label(self.lf_ex_tl, text="Font Color")
        self.lbl_ex_tl_font_color.pack(side="left", padx=5, pady=5)

        self.entry_ex_tl_font_color = ttk.Entry(self.lf_ex_tl, width=10)
        self.entry_ex_tl_font_color.pack(side="left", padx=5, pady=5)
        self.entry_ex_tl_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_font_color, self.entry_ex_tl_font_color.get(), self.root)
            or sj.savePartialSetting("tb_ex_tl_font_color", self.entry_ex_tl_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tl_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tl_bg_color = ttk.Label(self.lf_ex_tl, text="Background Color")
        self.lbl_ex_tl_bg_color.pack(side="left", padx=5, pady=5)

        self.entry_ex_tl_bg_color = ttk.Entry(self.lf_ex_tl, width=10)
        self.entry_ex_tl_bg_color.pack(side="left", padx=5, pady=5)
        self.entry_ex_tl_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_bg_color, self.entry_ex_tl_bg_color.get(), self.root) or sj.savePartialSetting("tb_ex_tl_bg_color", self.entry_ex_tl_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tl_bg_color.bind("<Key>", lambda e: "break")

        # PREVIEW'
        self.f_textbox_2 = ttk.Frame(self.ft_textbox)
        self.f_textbox_2.pack(side="top", fill="x", pady=5)

        self.f_textbox_3 = ttk.Frame(self.ft_textbox)
        self.f_textbox_3.pack(side="top", fill="x", pady=5)

        self.tb_preview_1 = tk.Text(
            self.f_textbox_2,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(sj.cache["tb_mw_tc_font"], sj.cache["tb_mw_tc_font_size"], "bold" if sj.cache["tb_mw_tc_font_bold"] else "normal"),
        )
        self.tb_preview_1.bind("<Key>", "break")
        self.tb_preview_1.insert("end", "TC Main window:\n" + PREVIEW_WORDS)
        self.tb_preview_1.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        self.tb_preview_2 = tk.Text(
            self.f_textbox_2,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(sj.cache["tb_mw_tl_font"], sj.cache["tb_mw_tl_font_size"], "bold" if sj.cache["tb_mw_tl_font_bold"] else "normal"),
        )
        self.tb_preview_2.bind("<Key>", "break")
        self.tb_preview_2.insert("end", "TL Main window:\n" + PREVIEW_WORDS)
        self.tb_preview_2.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        self.tb_preview_3 = tk.Text(
            self.f_textbox_3,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(sj.cache["tb_ex_tc_font"], sj.cache["tb_ex_tc_font_size"], "bold" if sj.cache["tb_ex_tc_font_bold"] else "normal"),
            foreground=sj.cache["tb_ex_tc_font_color"],
            background=sj.cache["tb_ex_tc_bg_color"],
        )
        self.tb_preview_3.bind("<Key>", "break")
        self.tb_preview_3.insert("end", "TC Subtitle window:\n" + PREVIEW_WORDS)
        self.tb_preview_3.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        self.tb_preview_4 = tk.Text(
            self.f_textbox_3,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(sj.cache["tb_ex_tl_font"], sj.cache["tb_ex_tl_font_size"], "bold" if sj.cache["tb_ex_tl_font_bold"] else "normal"),
            foreground=sj.cache["tb_ex_tl_font_color"],
            background=sj.cache["tb_ex_tl_bg_color"],
        )
        self.tb_preview_4.bind("<Key>", "break")
        self.tb_preview_4.insert("end", "TL Subtitle window:\n" + PREVIEW_WORDS)
        self.tb_preview_4.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        # ------------------ Variables ------------------
        # Flags
        gc.sw = self  # Add self to global class

        # ------------------ Functions ------------------
        self.on_close()  # hide window on start
        self.init_threaded()
        self.init_setting_once()
        self.bind_focus_on_frame_recursively(self.root)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

    # ------------------ Functions ------------------
    def init_threaded(self):
        """
        Init some startup function in a thread to avoid blocking
        """
        threading.Thread(target=self.deleteLogOnStart, daemon=True).start()
        threading.Thread(target=self.deleteTempOnStart, daemon=True).start()

    def save_win_size(self):
        """
        Save window size
        """
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w > 600 and h > 300:
            sj.savePartialSetting("sw_size", f"{w}x{h}")

    def on_close(self):
        self.save_win_size()
        self.root.withdraw()

    def show(self):
        self.root.after(0, self.root.deiconify)

        if not self.model_checked:
            threading.Thread(target=self.checkModelOnFirstSettingOpen, daemon=True).start()

    def bind_focus_on_frame_recursively(self, root_widget):
        widgets = root_widget.winfo_children()

        # now check if there are any children of the children
        for widget in widgets:
            if len(widget.winfo_children()) > 0:
                self.bind_focus_on_frame_recursively(widget)

            if isinstance(widget, tk.Frame) or isinstance(widget, ttk.Frame) or isinstance(widget, tk.LabelFrame):
                widget.bind("<Button-1>", lambda event: self.root.focus_set())  # type: ignore

    def init_setting_once(self):
        logger.setLevel(sj.cache["log_level"])
        # app
        cbtnInvoker(sj.cache["keep_log"], self.cbtn_keep_log)
        cbtnInvoker(sj.cache["debug_realtime_record"], self.cbtn_debug_realtime_record)
        cbtnInvoker(sj.cache["debug_translate"], self.cbtn_debug_translate)
        cbtnInvoker(sj.cache["verbose"], self.cbtn_verbose)
        cbtnInvoker(sj.cache["checkUpdateOnStart"], self.cbtn_update_on_start)
        cbtnInvoker(sj.cache["supress_hidden_to_tray"], self.cbtn_supress_hidden_to_tray)
        cbtnInvoker(sj.cache["supress_device_warning"], self.cbtn_supress_device_warning)
        cbtnInvoker(sj.cache["auto_open_dir_export"], self.cbtn_auto_open_export)
        if sj.cache["dir_export"] == "auto":
            self.default_export_path()
        else:
            self.entry_export.configure(state="normal")
            self.entry_export.insert(0, sj.cache["dir_export"])
            self.entry_export.configure(state="readonly")

        self.cb_log_level.set(sj.cache["log_level"])
        self.fill_theme()

        # tc
        self.entry_separate_text_with.delete(0, "end")
        self.entry_separate_text_with.insert(0, sj.cache["separate_with"])
        self.spn_buffer_mic.set(sj.cache["mic_maxBuffer"])
        self.spn_max_sentences.set(sj.cache["max_sentences"])
        self.spn_max_temp.set(sj.cache["max_temp"])
        self.spn_sample_rate.set(sj.cache["sample_rate"])
        self.spn_chunk_size.set(sj.cache["chunk_size"])
        self.spn_tc_rate.set(sj.cache["transcribe_rate"])
        cbtnInvoker(sj.cache["auto_sample_rate"], self.cbtn_auto_sample_rate)
        cbtnInvoker(sj.cache["auto_channels_amount"], self.cbtn_auto_channels_amount)
        cbtnInvoker(sj.cache["keep_temp"], self.cbtn_keep_temp)
        cbtnInvoker(sj.cache["enable_threshold"], self.cbtn_enable_threshold)
        cbtnInvoker(sj.cache["debug_energy"], self.cbtn_debug_energy)
        self.spn_threshold_mic.set(sj.cache["mic_energy_threshold"])

        # whisper settings
        cbtnInvoker(sj.cache["condition_on_previous_text"], self.cbtn_condition_on_previous_text)
        self.spn_compression_ratio_threshold.set(sj.cache["compression_ratio_threshold"])
        self.spn_logprob_threshold.set(sj.cache["logprob_threshold"])
        self.spn_no_speech_threshold.set(sj.cache["no_speech_threshold"])
        self.entry_initial_prompt.delete(0, "end")
        self.entry_initial_prompt.insert(0, sj.cache["initial_prompt"])
        self.entry_temperature.delete(0, "end")
        self.entry_temperature.insert(0, sj.cache["temperature"])
        self.entry_whisper_extra_args.delete(0, "end")
        self.entry_whisper_extra_args.insert(0, sj.cache["whisper_extra_args"])

        # tl
        self.entry_libre_key.delete(0, "end")
        self.entry_libre_key.insert(0, sj.cache["libre_api_key"])
        self.entry_libre_host.delete(0, "end")
        self.entry_libre_host.insert(0, sj.cache["libre_host"])
        self.entry_libre_port.delete(0, "end")
        self.entry_libre_port.insert(0, sj.cache["libre_port"])
        cbtnInvoker(sj.cache["libre_https"], self.cbtn_libre_https)

        # tb
        self.init_tb_settings(sj.cache)
        cbtnInvoker(sj.cache["tb_mw_tc_font_bold"], self.cbtn_mw_tc_font_bold)
        cbtnInvoker(sj.cache["tb_mw_tl_font_bold"], self.cbtn_mw_tl_font_bold)
        cbtnInvoker(sj.cache["tb_ex_tc_font_bold"], self.cbtn_ex_tc_font_bold)
        cbtnInvoker(sj.cache["tb_ex_tl_font_bold"], self.cbtn_ex_tl_font_bold)

        if platform.system() == "Windows":
            self.spn_buffer_speaker.set(sj.cache["speaker_maxBuffer"])
            self.spn_threshold_speaker.set(sj.cache["speaker_energy_threshold"])

    def tb_delete(self):
        self.entry_ex_tc_font_color.delete(0, "end")
        self.entry_ex_tc_bg_color.delete(0, "end")

        self.entry_ex_tl_font_color.delete(0, "end")
        self.entry_ex_tl_bg_color.delete(0, "end")

    def init_tb_settings(self, theSetting):
        self.tb_delete()
        self.spn_mw_tc_max.set(theSetting["tb_mw_tc_max"])
        self.cb_mw_tc_font.set(theSetting["tb_mw_tc_font"])
        self.spn_mw_tc_font_size.set(theSetting["tb_mw_tc_font_size"])

        self.spn_mw_tl_max.set(theSetting["tb_mw_tl_max"])
        self.cb_mw_tl_font.set(theSetting["tb_mw_tl_font"])
        self.spn_mw_tl_font_size.set(theSetting["tb_mw_tl_font_size"])

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
        if gc.mw is None:
            return

        gc.mw.tb_transcribed.configure(font=(self.cb_mw_tc_font.get(), int(self.spn_mw_tc_font_size.get()), "bold" if self.cbtn_mw_tc_font_bold.instate(["selected"]) else "normal"))
        self.tb_preview_1.configure(font=(self.cb_mw_tc_font.get(), int(self.spn_mw_tc_font_size.get()), "bold" if self.cbtn_mw_tc_font_bold.instate(["selected"]) else "normal"))

        gc.mw.tb_translated.configure(font=(self.cb_mw_tl_font.get(), int(self.spn_mw_tl_font_size.get()), "bold" if self.cbtn_mw_tl_font_bold.instate(["selected"]) else "normal"))
        self.tb_preview_2.configure(font=(self.cb_mw_tl_font.get(), int(self.spn_mw_tl_font_size.get()), "bold" if self.cbtn_mw_tl_font_bold.instate(["selected"]) else "normal"))

        assert gc.ex_tcw is not None
        gc.ex_tcw.labelText.configure(
            font=(self.cb_ex_tc_font.get(), int(self.spn_ex_tc_font_size.get()), "bold" if self.cbtn_ex_tc_font_bold.instate(["selected"]) else "normal"),
            foreground=self.entry_ex_tc_font_color.get(),
            background=self.entry_ex_tc_bg_color.get(),
        )
        self.tb_preview_3.configure(
            font=(self.cb_ex_tc_font.get(), int(self.spn_ex_tc_font_size.get()), "bold" if self.cbtn_ex_tc_font_bold.instate(["selected"]) else "normal"),
            foreground=self.entry_ex_tc_font_color.get(),
            background=self.entry_ex_tc_bg_color.get(),
        )

        assert gc.ex_tlw is not None
        gc.ex_tlw.labelText.configure(
            font=(self.cb_ex_tl_font.get(), int(self.spn_ex_tl_font_size.get()), "bold" if self.cbtn_ex_tl_font_bold.instate(["selected"]) else "normal"),
            foreground=self.entry_ex_tl_font_color.get(),
            background=self.entry_ex_tl_bg_color.get(),
        )
        self.tb_preview_4.configure(
            font=(self.cb_ex_tl_font.get(), int(self.spn_ex_tl_font_size.get()), "bold" if self.cbtn_ex_tl_font_bold.instate(["selected"]) else "normal"),
            foreground=self.entry_ex_tl_font_color.get(),
            background=self.entry_ex_tl_bg_color.get(),
        )

    def number_only(self, P):
        return P.isdigit()

    def number_only_float(self, P):
        try:
            float(P)
        except ValueError:
            return False
        return True

    def verifyMaxNumber(self, el, min: int, max: int, cb_func=None):
        # verify value only after user has finished typing
        self.root.after(1000, lambda: self.checkNumber(el, min, max, cb_func))

    def verifyMaxNumber_float(self, el, min: int, max: int, cb_func=None):
        # verify value only after user has finished typing
        self.root.after(1000, lambda: self.checkNumber(el, min, max, cb_func, True))

    def checkNumber(self, el, min: int, max: int, cb_func=None, converts_to_float=False):
        value = el.get()

        converts_to = float if converts_to_float else int
        if converts_to(value) > max:
            el.set(max)

        if converts_to(value) < min:
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

    def deleteTemp(self):
        # delete all temp wav files
        for file in os.listdir(dir_temp):
            if file.endswith(".wav"):
                try:
                    os.remove(os.path.join(dir_temp, file))
                except Exception as e:
                    logger.warning("Failed to delete temp file: " + file)
                    logger.warning("Reason " + str(e))

    def deleteLogOnStart(self):
        if not sj.cache["keep_log"]:
            self.deleteTheLog()

    def deleteTempOnStart(self):
        if not sj.cache["keep_temp"]:
            self.deleteTemp()

    def promptDeleteLog(self):
        # confirmation using mbox
        if mbox("Delete Log Files", "Are you sure you want to delete all log files?", 3, self.root):
            # delete all log files
            self.deleteTheLog()

            # confirmation using mbox
            mbox("Delete Log Files", "Log files deleted successfully!", 0, self.root)

    def model_check(self, model: str, btn: ttk.Button, withPopup=True) -> None:
        downloaded = verify_model(model)

        if not downloaded:
            if withPopup:
                mbox("Model not found", "Model not found or checksum does not match. You can press download to download the model.", 0, self.root)
            btn.configure(text="Download", command=lambda: self.modelDownload(model, btn))
        else:
            btn.configure(text="Downloaded", state=tk.DISABLED)

    def modelDownload(self, model: str, btn: ttk.Button) -> None:
        if self.checkingModel:
            return

        # if already downloading then return
        if gc.dl_thread and gc.dl_thread.is_alive():
            mbox("Already downloading", "Please wait for the current download to finish.", 0, self.root)
            return

        # verify first
        if verify_model(model):  # already downloaded
            btn.configure(text="Downloaded", state=tk.DISABLED)
            return

        # Download model
        try:

            def after_func():
                btn.configure(text="Downloaded", state=tk.DISABLED)

            gc.dl_thread = threading.Thread(target=download_model, args=(model, self.root, lambda: self.modelDownloadCancel(model, btn), after_func), daemon=True)
            gc.dl_thread.start()

            btn.configure(text="Downloading...", state=tk.DISABLED)
        except Exception as e:
            btn.configure(text="Download", command=lambda: self.modelDownload(model, btn), state=tk.NORMAL)
            mbox("Download error", f"Err details: {e}", 0, self.root)

    def modelDownloadCancel(self, model: str, btn: ttk.Button) -> None:
        if not mbox("Cancel confirmation", "Are you sure you want to cancel downloading?", 3, self.root):
            return

        btn.configure(text="Download", command=lambda: self.modelDownload(model, btn), state=tk.NORMAL)
        gc.cancel_dl = True  # Raise flag to stop

    def modelBtnChecker(self, model: str, btn: ttk.Button) -> None:
        """
        Helper to check if model is downloaded.
        It will first change btn state to disabled to prevent user from clicking it, set text to "Checking..."
        Then check it and change the text and state accordingly.
        """
        btn.configure(text="Checking...", state=tk.DISABLED)

        downloaded = verify_model(model)

        if not downloaded:
            btn.configure(text="Download", command=lambda: self.modelDownload(model, btn), state=tk.NORMAL)
        else:
            btn.configure(text="Downloaded", state=tk.DISABLED)

    def checkModelOnFirstSettingOpen(self):
        """
        Check if model is downloaded on first setting open.
        It need to be checked hardcodedly because for some reason if i try to use a map it keep referencing to the wrong button.
        """
        try:
            self.checkingModel = True
            self.modelBtnChecker("tiny", self.btn_interact_tiny)
            self.modelBtnChecker("tiny.en", self.btn_interact_tiny_eng)
            self.modelBtnChecker("base", self.btn_interact_base)
            self.modelBtnChecker("base.en", self.btn_interact_base_eng)
            self.modelBtnChecker("small", self.btn_interact_small)
            self.modelBtnChecker("small.en", self.btn_interact_small_eng)
            self.modelBtnChecker("medium", self.btn_interact_medium)
            self.modelBtnChecker("medium.en", self.btn_interact_medium_eng)
            self.modelBtnChecker("large-v1", self.btn_interact_large_v1)
            self.modelBtnChecker("large-v2", self.btn_interact_large_v2)
            self.model_checked = True
            self.first_check = False
        except Exception as e:
            logger.error("Failed to check model on first setting open")
            logger.exception(e)
            if self.first_check:
                # run this function again if it failed on first check but after 3 second
                logger.warning("Retrying to check model on first setting open")
                self.root.after(3000, lambda: threading.Thread(target=self.checkModelOnFirstSettingOpen, daemon=True).start())
        finally:
            self.checkingModel = False

    def get_the_threshold(self, device: Literal["mic", "speaker"]) -> None:
        self.getting_threshold = True
        threshold = getDeviceAverageThreshold(device)
        self.spn_threshold_mic.set(str(int(threshold)))
        sj.savePartialSetting("mic_energy_threshold" if device == "mic" else "speaker_energy_threshold", threshold)
        self.getting_threshold = False

    def micAutoThreshold(self):
        """
        Prompt the user to record for 5 seconds and get the optimal threshold for the mic.
        """
        if self.getting_threshold:
            mbox("Already getting threshold", "Please wait until the current threshold is calculated.", 1)
            return

        if mbox(
            "Auto Threshold - Mic",
            "After you press `yes` the program will record for 5 seconds and try to get the optimal threshold\n\nTry to keep the device silent to avoid inaccuracy\n\nSelected device: "
            + sj.cache["mic"]
            + "\n\n*Press no to cancel",
            3,
            self.root,
        ):
            # run in thread
            thread = threading.Thread(target=self.get_the_threshold, args=("mic",), daemon=True)
            thread.start()

            # show countdown window and wait for it to close
            CountdownWindow(self.root, 5, "Getting threshold...", "Getting threshold for mic")

    def speakerAutoThreshold(self):
        """
        Prompt the user to record for 5 seconds and get the optimal threshold for the speaker.
        """
        if self.getting_threshold:
            mbox("Already getting threshold", "Please wait until the current threshold is calculated.", 1)
            return

        if mbox(
            "Auto Threshold - Speaker",
            "After you press `yes` the program will record for 5 seconds and try to get the optimal threshold\n\nTry to keep the device silent to avoid inaccuracy\n\nSelected device: "
            + sj.cache["speaker"]
            + "\n\n*Press no to cancel",
            3,
            self.root,
        ):
            # run in thread
            thread = threading.Thread(target=self.get_the_threshold, args=("speaker",), daemon=True)
            thread.start()

            # show countdown window and wait for it to close
            CountdownWindow(self.root, 5, "Getting threshold...", "Getting threshold for speaker")

    def fill_theme(self):
        self.cb_theme["values"] = gc.theme_lists
        self.cb_theme.set(sj.cache["theme"])
        self.initial_theme = sj.cache["theme"]
        self.entry_theme.pack_forget()
        self.btn_theme_add.pack_forget()
        self.lbl_notice_theme.pack_forget()

    def cb_theme_change(self, _event=None):
        if self.cb_theme.get() == "custom":
            self.entry_theme.pack(side="left", padx=5, pady=5, fill="x", expand=True)
            self.entry_theme.delete(0, "end")
            self.btn_theme_add.pack(side="left", padx=5, pady=5)
        else:
            self.entry_theme.pack_forget()
            self.entry_theme.delete(0, "end")
            self.btn_theme_add.pack_forget()

            if self.initial_theme != self.cb_theme.get():
                self.lbl_notice_theme.pack(side="left", padx=5, pady=5)
            else:
                self.lbl_notice_theme.pack_forget()

            # save
            sj.savePartialSetting("theme", self.cb_theme.get())

            # set the theme
            set_ui_style(self.cb_theme.get())

    def add_theme(self):
        theme_name = self.entry_theme.get()
        if theme_name == "":
            mbox("Error", "Theme name cannot be empty", 0, self.root)
            return

        if theme_name in gc.theme_lists:
            mbox("Error", "Theme name already exist", 0, self.root)
            return

        if set_ui_style(theme_name, self.root):
            # add the theme to the list
            gc.theme_lists.append(theme_name)

            # save the theme
            sj.savePartialSetting("theme", theme_name)

            # fill the theme combobox
            self.fill_theme()
        else:
            # set to inital theme on this setting
            self.cb_theme.current(0)
            self.entry_theme.pack_forget()
            self.btn_theme_add.pack_forget()

        # if success, show notice
        # if fail also show. This is because if it fail it will fallback to the default theme
        self.lbl_notice_theme.pack(side="left", padx=5, pady=5)

    def log_level_change(self, _event=None):
        sj.savePartialSetting("log_level", self.cb_log_level.get())
        logger.setLevel(self.cb_log_level.get())

    def change_export_path(self):
        path = filedialog.askdirectory()
        if path != "":
            sj.savePartialSetting("dir_export", path)
            self.entry_export.configure(state="normal")
            self.entry_export.delete(0, "end")
            self.entry_export.insert(0, path)
            self.entry_export.configure(state="readonly")

    def default_export_path(self):
        self.entry_export.configure(state="normal")
        self.entry_export.delete(0, "end")
        self.entry_export.insert(0, dir_export)
        self.entry_export.configure(state="readonly")
        sj.savePartialSetting("dir_export", "auto")

    def clear_export(self):
        if mbox("Clear Export Folder", "Are you sure you want to clear the export folder?", 3, self.root):
            # get all the files in the export folder
            files = os.listdir(sj.cache["dir_export"])
            for file in files:
                os.remove(os.path.join(sj.cache["dir_export"], file))

    def verifyWhisperArgs(self):
        # get the values
        success, data = convert_str_options_to_dict(self.entry_whisper_extra_args.get())

        if not success:
            mbox("Error", f"Invalid arguments detected.\nDetails: {data}", 0, self.root)
        else:
            mbox("Success", f"Arguments are valid\nParsed: {data}", 0, self.root)

    def verifyTemp(self):
        # get values
        success, data = get_temperature(self.entry_temperature.get())

        if not success:
            mbox("Error", f"Invalid arguments detected.\nDetails: {data}", 0, self.root)
        else:
            mbox("Success", f"Arguments are valid\nParsed: {data}", 0, self.root)
