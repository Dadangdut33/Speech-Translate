import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Union
from datetime import datetime

from speech_translate.globals import sj, gc, dir_log, dir_temp, dir_export
from speech_translate.custom_logging import logger, current_log
from speech_translate.utils.helper import filename_only, popup_menu, emoji_img, up_first_case
from speech_translate.utils.model_download import verify_model, download_model, get_default_download_root
from speech_translate.utils.helper import start_file, cbtn_invoker
from speech_translate.utils.style import set_ui_style
from speech_translate.components.custom.message import MBoxText, mbox
from speech_translate.components.custom.tooltip import CreateToolTipOnText, tk_tooltip, tk_tooltips


class SettingGeneral:
    """
    General tab in setting window.
    """

    def __init__(self, root: tk.Toplevel, master_frame: Union[ttk.Frame, tk.Frame]):
        self.root = root
        self.master = master_frame
        self.initial_theme = ""
        self.checkingModel = False
        self.model_checked = False
        self.first_check = True
        self.folder_emoji = emoji_img(13, " 📂")
        self.open_emoji = emoji_img(13, "     ↗️")
        self.trash_emoji = emoji_img(13, "     🗑️")
        self.reset_emoji = emoji_img(13, " 🔄")
        self.wrench_emoji = emoji_img(16, "     🛠️")
        self.question_emoji = emoji_img(16, "❔")

        # ------------------ General ------------------
        # app
        self.lf_application = tk.LabelFrame(self.master, text="• Application")
        self.lf_application.pack(side="top", fill="x", padx=5, pady=5)

        self.f_application_1 = ttk.Frame(self.lf_application)
        self.f_application_1.pack(side="top", fill="x", padx=5)

        self.f_application_2 = ttk.Frame(self.lf_application)
        self.f_application_2.pack(side="top", fill="x", padx=5)

        self.f_application_3 = ttk.Frame(self.lf_application)
        self.f_application_3.pack(side="top", fill="x", padx=5)

        self.cbtn_update_on_start = ttk.Checkbutton(
            self.f_application_1,
            text="Check for update on start",
            command=lambda: sj.save_key("checkUpdateOnStart", self.cbtn_update_on_start.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_update_on_start.pack(side="left", padx=5, pady=5)

        self.cbtn_supress_hidden_to_tray = ttk.Checkbutton(
            self.f_application_1,
            text="Supress hidden to tray notif",
            command=lambda: sj.save_key("supress_hidden_to_tray", self.cbtn_supress_hidden_to_tray.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_supress_hidden_to_tray.pack(side="left", padx=5, pady=5)

        self.cbtn_supress_device_warning = ttk.Checkbutton(
            self.f_application_1,
            text="Supress device warning",
            command=lambda: sj.save_key("supress_device_warning", self.cbtn_supress_device_warning.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_supress_device_warning.pack(side="left", padx=5, pady=5)
        tk_tooltip(
            self.cbtn_supress_device_warning,
            "Supress warning notification that usually shows up when no input device is detected.",
        )

        self.lbl_notice_theme = ttk.Label(
            self.f_application_1, text="— Might need to reload the app for the changes to take effect."
        )
        self.lbl_notice_theme.pack(side="left", padx=5, pady=5)

        # theme
        self.lbl_theme = ttk.Label(self.f_application_2, text="Theme")
        self.lbl_theme.pack(side="left", padx=5, pady=5)

        self.cb_theme = ttk.Combobox(self.f_application_2, values=["dummy list"], state="readonly")
        self.cb_theme.pack(side="left", padx=5, pady=5)
        self.cb_theme.bind("<<ComboboxSelected>>", self.cb_theme_change)
        tk_tooltips(
            [self.cb_theme, self.lbl_theme],
            "Set theme for app.\n\nThe topmost selection is your default tkinter os theme."
            "\nTo add custom theme you can read the readme.txt in the theme folder."
            "\n\nMight need to reload the app for the changes to take effect.",
            wrapLength=500,
        )

        self.entry_theme = ttk.Entry(self.f_application_2)
        self.entry_theme.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        tk_tooltip(
            self.entry_theme,
            "Set the custom theme name if the one from dropdown is not working."
            "\n\nThe theme name should be according to the `set_theme` parameter in the .tcl folder of the theme."
            "\n\nMight need to reload the app for the changes to take effect.",
            wrapLength=500,
        )

        self.btn_theme_add = ttk.Button(self.f_application_2, text="Add", command=self.add_theme)
        self.btn_theme_add.pack(side="left", padx=5, pady=5)
        tk_tooltip(
            self.btn_theme_add,
            "Add custom theme.\n\nThe theme name should be according to the `set_theme` parameter in the .tcl folder of the theme."
            "\n\nMight need to reload the app for the changes to take effect.",
            wrapLength=500,
        )

        # --------------------
        # export
        self.lf_export = tk.LabelFrame(self.master, text="• Export")
        self.lf_export.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_1 = ttk.Frame(self.lf_export)
        self.f_export_1.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_2 = ttk.Frame(self.lf_export)
        self.f_export_2.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_3 = ttk.Frame(self.lf_export)
        self.f_export_3.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_4 = ttk.Frame(self.lf_export)
        self.f_export_4.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_5 = ttk.Frame(self.lf_export)
        self.f_export_5.pack(side="top", fill="x", padx=5, pady=5)

        self.lbl_export = ttk.Label(self.f_export_1, text="Export Folder", width=16)
        self.lbl_export.pack(side="left", padx=5, pady=5)

        self.entry_export = ttk.Entry(self.f_export_1)
        self.entry_export.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        tk_tooltip(self.entry_export, "The folder where exported text from import file are saved.")

        self.btn_export_config = ttk.Button(
            self.f_export_1,
            image=self.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_config_export),
        )
        self.btn_export_config.pack(side="left", padx=5, pady=5)

        self.menu_config_export = tk.Menu(self.master, tearoff=0)
        self.menu_config_export.add_command(
            label="Open", image=self.open_emoji, compound="left", command=lambda: start_file(self.entry_export.get())
        )
        self.menu_config_export.add_separator()
        self.menu_config_export.add_command(
            label="Change Folder",
            image=self.folder_emoji,
            compound="left",
            command=lambda: self.change_path("dir_export", self.entry_export),
        )
        self.menu_config_export.add_command(
            label="Set Back to Default",
            image=self.reset_emoji,
            compound="left",
            command=lambda: self.path_default("dir_export", self.entry_export, dir_export),
        )
        self.menu_config_export.add_separator()
        self.menu_config_export.add_command(
            label="Empty Export Folder", image=self.trash_emoji, compound="left", command=lambda: self.clear_export()
        )

        self.cbtn_auto_open_export = ttk.Checkbutton(
            self.f_export_2,
            text="Auto open export folder",
            command=lambda: sj.save_key("auto_open_dir_export", self.cbtn_auto_open_export.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_auto_open_export.pack(side="left", padx=5)
        tk_tooltip(self.cbtn_auto_open_export, "Auto open the export folder after file import")

        def keybind_num(event: tk.Event, save_to: str, widget: ttk.Entry):
            vsym = event.keysym
            vw = widget.get()
            v = event.char
            try:
                # check number or not
                int(v)  # pressed key
                sj.save_key(save_to, str(vw))
            except ValueError:
                # check value
                if vw == "":  # if empty
                    logger.debug("Empty")
                    sj.save_key(save_to, "")
                    return "break"
                elif vsym == "minus":  # if minus
                    logger.debug("Minus")
                    if "-" in vw:
                        replaced = vw.replace("-", "")
                        widget.delete(0, "end")
                        widget.insert(0, replaced)
                        sj.save_key(save_to, replaced)
                        return "break"
                    else:
                        replaced = "-" + vw
                        widget.delete(0, "end")
                        widget.insert(0, replaced)
                        sj.save_key(save_to, replaced)
                        return "break"

                # check pressed key
                if v != "\x08" and v != "":  # other than backspace and empty is not allowed
                    return "break"

        self.lbl_slice_file_start = ttk.Label(self.f_export_3, text="Slice file start", width=16)
        self.lbl_slice_file_start.pack(side="left", padx=5)
        self.entry_slice_file_start = ttk.Entry(self.f_export_3)
        self.entry_slice_file_start.bind("<Key>", lambda e: keybind_num(e, "file_slice_start", self.entry_slice_file_start))
        self.entry_slice_file_start.bind("<KeyRelease>", lambda e: self.update_preview_export_format())
        self.entry_slice_file_start.pack(side="left", padx=5)

        self.lbl_slice_file_end = ttk.Label(self.f_export_3, text="Slice file end", width=16)
        self.lbl_slice_file_end.pack(side="left", padx=5)
        self.entry_slice_file_end = ttk.Entry(self.f_export_3)
        self.entry_slice_file_end.bind("<Key>", lambda e: keybind_num(e, "file_slice_end", self.entry_slice_file_end))
        self.entry_slice_file_end.bind("<KeyRelease>", lambda e: self.update_preview_export_format())
        self.entry_slice_file_end.pack(side="left", padx=5)

        self.lbl_export_format = ttk.Label(self.f_export_4, text="Export format", width=16)
        self.lbl_export_format.pack(side="left", padx=5)
        self.entry_export_format = ttk.Entry(self.f_export_4)
        self.entry_export_format.bind(
            "<KeyRelease>",
            lambda e: sj.save_key("export_format", self.entry_export_format.get()) or self.update_preview_export_format(),
        )
        self.entry_export_format.pack(side="left", padx=5, fill="x", expand=True)

        available_params = (
            "Default value: %Y-%m-%d %H_%M {file}_{task}"
            "\n\nAvailable parameters:"
            "{file}"
            "\nWill be replaced with the file name"
            "\n\n{task}"
            "\nWill be replaced with the task name. (transcribe or translate)"
            "\n\n{task-short}"
            "\nWill be replaced with the task name but shorten. (tc or tl)"
            "\n\n{lang-source}"
            "\nWill be replaced with the source language"
            "\n\n{lang-target}"
            "\nWill be replaced with the target language"
            "\n\n{model}"
            "\nWill be replaced with the model name"
            "\n\n{engine}"
            "\nWill be replaced with the translation engine name"
        )
        self.btn_help_export_format = ttk.Button(
            self.f_export_4,
            image=self.question_emoji,
            command=lambda: MBoxText("export-format", self.root, "Export formats", available_params),
            width=3,
        )
        self.btn_help_export_format.pack(side="left", padx=5)

        self.lbl_preview_export_format = ttk.Label(self.f_export_5, text="", width=16)  # padding helper
        self.lbl_preview_export_format.pack(side="left", padx=5, pady=(0, 5))

        self.lbl_preview_export_format_result = ttk.Label(self.f_export_5, text="...", foreground="gray")
        self.lbl_preview_export_format_result.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.lbl_preview_export_format_result,
            "Preview of the export format with the current settings",
        )
        # --------------------
        # log
        self.lf_logging = tk.LabelFrame(self.master, text="• Logging")
        self.lf_logging.pack(side="top", fill="x", padx=5, pady=5)

        self.f_logging_1 = ttk.Frame(self.lf_logging)
        self.f_logging_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_2 = ttk.Frame(self.lf_logging)
        self.f_logging_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_3 = ttk.Frame(self.lf_logging)
        self.f_logging_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_4 = ttk.Frame(self.lf_logging)
        self.f_logging_4.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_log = ttk.Label(self.f_logging_1, text="Log Directory", width=16)
        self.lbl_log.pack(side="left", padx=5)

        self.entry_log = ttk.Entry(self.f_logging_1)
        self.entry_log.pack(side="left", padx=5, fill="x", expand=True)
        tk_tooltip(self.entry_log, "Directory of the app's log file.")

        self.btn_log_config = ttk.Button(
            self.f_logging_1,
            image=self.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_config_log),
        )
        self.btn_log_config.pack(side="left", padx=5, pady=5)

        self.menu_config_log = tk.Menu(self.master, tearoff=0)
        self.menu_config_log.add_command(
            label="Open", image=self.open_emoji, compound="left", command=lambda: start_file(dir_log)
        )
        self.menu_config_log.add_separator()
        self.menu_config_log.add_command(
            label="Change Folder",
            image=self.folder_emoji,
            compound="left",
            command=lambda: self.change_path("dir_log", self.entry_log),
        )
        self.menu_config_log.add_command(
            label="Set Back to Default",
            image=self.reset_emoji,
            compound="left",
            command=lambda: self.path_default("dir_log", self.entry_log, dir_log),
        )
        self.menu_config_log.add_separator()
        self.menu_config_log.add_command(
            label="Empty Log Folder", image=self.trash_emoji, compound="left", command=lambda: self.promptDeleteLog()
        )

        self.cbtn_verbose = ttk.Checkbutton(
            self.f_logging_2,
            text="Verbose logging for whisper",
            command=lambda: sj.save_key("verbose", self.cbtn_verbose.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_verbose.pack(side="left", padx=5)

        self.cbtn_keep_log = ttk.Checkbutton(
            self.f_logging_3,
            text="Keep log files",
            command=lambda: sj.save_key("keep_log", self.cbtn_keep_log.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_keep_log.pack(side="left", padx=5)

        self.lbl_loglevel = ttk.Label(self.f_logging_3, text="— Log level")
        self.lbl_loglevel.pack(side="left", padx=(0, 5))

        self.cb_log_level = ttk.Combobox(
            self.f_logging_3, values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], state="readonly"
        )
        self.cb_log_level.pack(side="left", padx=0)

        self.cbtn_debug_realtime_record = ttk.Checkbutton(
            self.f_logging_4,
            text="Debug realtime record",
            command=lambda: sj.save_key("debug_realtime_record", self.cbtn_debug_realtime_record.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_debug_realtime_record.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_debug_realtime_record,
            "Show some debugging process of the realtime record.\n\n" "Enabling will probably slow down the app.",
        )

        self.cbtn_debug_db = ttk.Checkbutton(
            self.f_logging_4,
            text="Debug audio db",
            command=lambda: sj.save_key("debug_db", self.cbtn_debug_db.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_debug_db.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_debug_db,
            "Show audio db in the console.\n\nEnabling will probably slow down the app.",
        )

        self.cbtn_debug_translate = ttk.Checkbutton(
            self.f_logging_4,
            text="Debug translate",
            command=lambda: sj.save_key("debug_translate", self.cbtn_debug_translate.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_debug_translate.pack(side="left", padx=5, pady=(0, 5))

        # model
        self.ft1lf_model = tk.LabelFrame(self.master, text="• Model")
        self.ft1lf_model.pack(side="top", fill="x", padx=5, pady=5)

        # label model location
        self.f_model_1 = ttk.Frame(self.ft1lf_model)
        self.f_model_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_model_2 = ttk.Frame(self.ft1lf_model)
        self.f_model_2.pack(side="top", fill="x", padx=5)

        self.f_model_3 = ttk.Frame(self.ft1lf_model)
        self.f_model_3.pack(side="top", fill="x", padx=5)

        self.lbl_model = ttk.Label(self.f_model_1, text="Model Directory ", width=16)
        self.lbl_model.pack(side="left", padx=5)

        self.entry_model = ttk.Entry(self.f_model_1, cursor="hand2", width=100)
        self.entry_model.pack(side="left", padx=5, fill="x", expand=True)
        tk_tooltip(self.entry_model, "Location of the model file.")

        self.btn_model_config = ttk.Button(
            self.f_model_1,
            image=self.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_config_model),
        )
        self.btn_model_config.pack(side="left", padx=5, pady=5)

        self.menu_config_model = tk.Menu(self.master, tearoff=0)
        self.menu_config_model.add_command(
            label="Open", image=self.open_emoji, compound="left", command=lambda: start_file(sj.cache["dir_model"])
        )
        self.menu_config_model.add_separator()
        self.menu_config_model.add_command(
            label="Change Folder",
            image=self.folder_emoji,
            compound="left",
            command=lambda: self.change_path("dir_model", self.entry_model),
        )
        self.menu_config_model.add_command(
            label="Set Back to Default",
            image=self.reset_emoji,
            compound="left",
            command=lambda: self.path_default("dir_model", self.entry_model, get_default_download_root()),
        )

        # small
        self.lf_md_dl1 = ttk.Frame(self.f_model_2)
        self.lf_md_dl1.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_tiny = ttk.LabelFrame(self.lf_md_dl1, text="Tiny")
        self.lf_model_tiny.pack(side="left")

        self.btn_interact_tiny = ttk.Button(
            self.lf_model_tiny, text="Verify", command=lambda: self.model_check("tiny", self.btn_interact_tiny)
        )
        self.btn_interact_tiny.pack(side="left", padx=5)

        # small en
        self.lf_md_dl2 = ttk.Frame(self.f_model_2)
        self.lf_md_dl2.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_tiny_eng = ttk.LabelFrame(self.lf_md_dl2, text="Tiny (en)")
        self.lf_model_tiny_eng.pack(side="left")

        self.btn_interact_tiny_eng = ttk.Button(
            self.lf_model_tiny_eng,
            text="Verify",
            command=lambda: self.model_check("tiny.en", self.btn_interact_tiny_eng),
        )
        self.btn_interact_tiny_eng.pack(side="left", padx=5)

        # base
        self.lf_md_dl3 = ttk.Frame(self.f_model_2)
        self.lf_md_dl3.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_base = ttk.LabelFrame(self.lf_md_dl3, text="Base")
        self.lf_model_base.pack(side="left")

        self.btn_interact_base = ttk.Button(
            self.lf_model_base, text="Verify", command=lambda: self.model_check("base", self.btn_interact_base)
        )
        self.btn_interact_base.pack(side="left", padx=5)

        # base en
        self.lf_md_dl4 = ttk.Frame(self.f_model_2)
        self.lf_md_dl4.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_base_eng = ttk.LabelFrame(self.lf_md_dl4, text="Base (en)")
        self.lf_model_base_eng.pack(side="left")

        self.btn_interact_base_eng = ttk.Button(
            self.lf_model_base_eng,
            text="Verify",
            command=lambda: self.model_check("base.en", self.btn_interact_base_eng),
        )
        self.btn_interact_base_eng.pack(side="left", padx=5)

        # small
        self.lf_md_dl5 = ttk.Frame(self.f_model_2)
        self.lf_md_dl5.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_small = ttk.LabelFrame(self.lf_md_dl5, text="Small")
        self.lf_model_small.pack(side="left")

        self.btn_interact_small = ttk.Button(
            self.lf_model_small, text="Verify", command=lambda: self.model_check("small", self.btn_interact_small)
        )
        self.btn_interact_small.pack(side="left", padx=5)

        # small en
        self.lf_md_dl6 = ttk.Frame(self.f_model_2)
        self.lf_md_dl6.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_small_eng = ttk.LabelFrame(self.lf_md_dl6, text="Small (en)")
        self.lf_model_small_eng.pack(side="left")

        self.btn_interact_small_eng = ttk.Button(
            self.lf_model_small_eng,
            text="Verify",
            command=lambda: self.model_check("small.en", self.btn_interact_small_eng),
        )
        self.btn_interact_small_eng.pack(side="left", padx=5)

        # medium
        self.lf_md_dl7 = ttk.Frame(self.f_model_2)
        self.lf_md_dl7.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_medium = ttk.LabelFrame(self.lf_md_dl7, text="Medium")
        self.lf_model_medium.pack(side="left")

        self.btn_interact_medium = ttk.Button(
            self.lf_model_medium, text="Verify", command=lambda: self.model_check("medium", self.btn_interact_medium)
        )
        self.btn_interact_medium.pack(side="left", padx=5)

        # medium en
        self.lf_md_dl8 = ttk.Frame(self.f_model_2)
        self.lf_md_dl8.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_medium_eng = ttk.LabelFrame(self.lf_md_dl8, text="Medium (en)")
        self.lf_model_medium_eng.pack(side="left")

        self.btn_interact_medium_eng = ttk.Button(
            self.lf_model_medium_eng,
            text="Verify",
            command=lambda: self.model_check("medium.en", self.btn_interact_medium_eng),
        )
        self.btn_interact_medium_eng.pack(side="left", padx=5)

        # large v1
        self.lf_md_dl9 = ttk.Frame(self.f_model_2)
        self.lf_md_dl9.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_large_v1 = ttk.LabelFrame(self.lf_md_dl9, text="Large (v1)")
        self.lf_model_large_v1.pack(side="left")

        self.btn_interact_large_v1 = ttk.Button(
            self.lf_model_large_v1,
            text="Verify",
            command=lambda: self.model_check("large-v1", self.btn_interact_large_v1),
        )
        self.btn_interact_large_v1.pack(side="left", padx=5)

        # large v2
        self.lf_md_dl10 = ttk.Frame(self.f_model_2)
        self.lf_md_dl10.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model_large_v2 = ttk.LabelFrame(self.lf_md_dl10, text="Large (v2)")
        self.lf_model_large_v2.pack(side="left")

        self.btn_interact_large_v2 = ttk.Button(
            self.lf_model_large_v2,
            text="Verify",
            command=lambda: self.model_check("large-v2", self.btn_interact_large_v2),
        )
        self.btn_interact_large_v2.pack(side="left", padx=5)

        # ------------------ Functions ------------------
        self.init_setting_once()

    # ------------------ Functions ------------------
    def init_setting_once(self):
        logger.setLevel(sj.cache["log_level"])
        # app
        cbtn_invoker(sj.cache["keep_log"], self.cbtn_keep_log)
        cbtn_invoker(sj.cache["debug_realtime_record"], self.cbtn_debug_realtime_record)
        cbtn_invoker(sj.cache["debug_db"], self.cbtn_debug_db)
        cbtn_invoker(sj.cache["debug_translate"], self.cbtn_debug_translate)
        cbtn_invoker(sj.cache["verbose"], self.cbtn_verbose)
        cbtn_invoker(sj.cache["checkUpdateOnStart"], self.cbtn_update_on_start)
        cbtn_invoker(sj.cache["supress_hidden_to_tray"], self.cbtn_supress_hidden_to_tray)
        cbtn_invoker(sj.cache["supress_device_warning"], self.cbtn_supress_device_warning)
        cbtn_invoker(sj.cache["auto_open_dir_export"], self.cbtn_auto_open_export)

        self.entry_slice_file_start.insert(0, sj.cache["file_slice_start"])
        self.entry_slice_file_end.insert(0, sj.cache["file_slice_end"])
        self.entry_export_format.insert(0, sj.cache["export_format"])
        self.update_preview_export_format()

        if sj.cache["dir_export"] == "auto":
            self.path_default("dir_export", self.entry_export, dir_export, save=False, prompt=False)
        else:
            self.entry_export.configure(state="normal")
            self.entry_export.insert(0, sj.cache["dir_export"])
            self.entry_export.configure(state="readonly")

        if sj.cache["dir_log"] == "auto":
            self.path_default("dir_log", self.entry_log, dir_log, save=False, prompt=False)
        else:
            self.entry_log.configure(state="normal")
            self.entry_log.insert(0, sj.cache["dir_log"])
            self.entry_log.configure(state="readonly")

        if sj.cache["dir_model"] == "auto":
            self.path_default("dir_model", self.entry_model, get_default_download_root(), save=False, prompt=False)
        else:
            self.entry_model.configure(state="normal")
            self.entry_model.insert(0, sj.cache["dir_model"])
            self.entry_model.configure(state="readonly")

        self.cb_log_level.set(sj.cache["log_level"])
        self.fill_theme()

    def update_preview_export_format(self):
        filename = filename_only("this is an example video or audio file.mp4")
        task = "transcribe"
        short_task = "tc"
        slice_start = int(self.entry_slice_file_start.get()) if self.entry_slice_file_start.get() != "" else None
        slice_end = int(self.entry_slice_file_end.get()) if self.entry_slice_file_end.get() != "" else None

        assert gc.mw is not None
        save_name = datetime.now().strftime(self.entry_export_format.get())
        save_name = save_name.replace("{file}", filename[slice_start:slice_end])
        save_name = save_name.replace("{lang-source}", gc.mw.cb_sourceLang.get())
        save_name = save_name.replace("{lang-target}", gc.mw.cb_targetLang.get())
        save_name = save_name.replace("{model}", gc.mw.cb_model.get())
        save_name = save_name.replace("{engine}", gc.mw.cb_engine.get())
        save_name = save_name.replace("{task}", task)
        save_name = save_name.replace("{task-short}", short_task)

        self.lbl_preview_export_format_result.configure(text=save_name)

    def delete_log(self):
        # delete all log files
        for file in os.listdir(dir_log):
            if file.endswith(".log"):
                try:
                    os.remove(os.path.join(dir_log, file))
                except Exception as e:
                    if file != current_log:  # show warning only if the fail to delete is not the current log
                        logger.warning("Failed to delete log file: " + file)
                        logger.warning("Reason " + str(e))

    def delete_temp(self):
        # delete all temp wav files
        for file in os.listdir(dir_temp):
            if file.endswith(".wav"):
                try:
                    os.remove(os.path.join(dir_temp, file))
                except Exception as e:
                    logger.warning("Failed to delete temp file: " + file)
                    logger.warning("Reason " + str(e))

    def delete_log_on_start(self):
        if not sj.cache["keep_log"]:
            self.delete_log()

    def delete_temp_on_start(self):
        if not sj.cache["keep_temp"]:
            self.delete_temp()

    def promptDeleteLog(self):
        # confirmation using mbox
        if mbox("Delete Log Files", "Are you sure you want to delete all log files?", 3, self.root):
            # delete all log files
            self.delete_log()

            # confirmation using mbox
            mbox("Delete Log Files", "Log files deleted successfully!", 0, self.root)

    def model_check(self, model: str, btn: ttk.Button, withPopup=True) -> None:
        downloaded = verify_model(model)

        if not downloaded:
            if withPopup:
                mbox(
                    "Model not found",
                    "Model not found or checksum does not match. You can press download to download the model.",
                    0,
                    self.root,
                )
            btn.configure(text="Download", command=lambda: self.model_download(model, btn))
        else:
            btn.configure(text="Downloaded", state=tk.DISABLED)

    def model_download(self, model: str, btn: ttk.Button) -> None:
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

            gc.dl_thread = threading.Thread(
                target=download_model,
                args=(model, self.root, lambda: self.cancel_download(model, btn), after_func),
                daemon=True,
            )
            gc.dl_thread.start()

            btn.configure(text="Downloading...", state=tk.DISABLED)
        except Exception as e:
            btn.configure(text="Download", command=lambda: self.model_download(model, btn), state=tk.NORMAL)
            mbox("Download error", f"Err details: {e}", 0, self.root)

    def cancel_download(self, model: str, btn: ttk.Button) -> None:
        if not mbox("Cancel confirmation", "Are you sure you want to cancel downloading?", 3, self.root):
            return

        btn.configure(text="Download", command=lambda: self.model_download(model, btn), state=tk.NORMAL)
        gc.cancel_dl = True  # Raise flag to stop

    def model_btn_checker(self, model: str, btn: ttk.Button) -> None:
        """
        Helper to check if model is downloaded.
        It will first change btn state to disabled to prevent user from clicking it, set text to "Checking..."
        Then check it and change the text and state accordingly.
        """
        btn.configure(text="Checking...", state=tk.DISABLED)

        downloaded = verify_model(model)

        if not downloaded:
            btn.configure(text="Download", command=lambda: self.model_download(model, btn), state=tk.NORMAL)
        else:
            btn.configure(text="Downloaded", state=tk.DISABLED)

    def check_model_on_first_open(self):
        """
        Check if model is downloaded on first setting open.
        It need to be checked hardcodedly because for some reason if i try to use a map it keep referencing to the wrong button.
        """
        try:
            self.checkingModel = True
            self.model_btn_checker("tiny", self.btn_interact_tiny)
            self.model_btn_checker("tiny.en", self.btn_interact_tiny_eng)
            self.model_btn_checker("base", self.btn_interact_base)
            self.model_btn_checker("base.en", self.btn_interact_base_eng)
            self.model_btn_checker("small", self.btn_interact_small)
            self.model_btn_checker("small.en", self.btn_interact_small_eng)
            self.model_btn_checker("medium", self.btn_interact_medium)
            self.model_btn_checker("medium.en", self.btn_interact_medium_eng)
            self.model_btn_checker("large-v1", self.btn_interact_large_v1)
            self.model_btn_checker("large-v2", self.btn_interact_large_v2)
            self.model_checked = True
            self.first_check = False
        except Exception as e:
            logger.error("Failed to check model on first setting open")
            logger.exception(e)
            if self.first_check:
                # run this function again if it failed on first check but after 3 second
                logger.warning("Retrying to check model on first setting open")
                self.root.after(3000, lambda: threading.Thread(target=self.check_model_on_first_open, daemon=True).start())
        finally:
            self.checkingModel = False

    def fill_theme(self):
        self.cb_theme["values"] = gc.theme_lists
        self.cb_theme.set(sj.cache["theme"])
        self.initial_theme = sj.cache["theme"]
        self.entry_theme.pack_forget()
        self.btn_theme_add.pack_forget()
        self.lbl_notice_theme.pack_forget()

    def prompt_restart_app_after_changing_theme(self):
        if mbox(
            "Restart confirmation",
            "It is recommended to restart the app for the theme to fully take effect. Do you want to restart now?",
            3,
            self.root,
        ):
            #
            assert gc.mw is not None
            gc.mw.restart_app()

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
            sj.save_key("theme", self.cb_theme.get())

            self.prompt_restart_app_after_changing_theme()

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
            sj.save_key("theme", theme_name)

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
        sj.save_key("log_level", self.cb_log_level.get())
        logger.setLevel(self.cb_log_level.get())

    def change_path(self, key: str, element: ttk.Entry):
        path = filedialog.askdirectory()
        if path != "":
            sj.save_key(key, path)
            element.configure(state="normal")
            element.delete(0, "end")
            element.insert(0, path)
            element.configure(state="readonly")

    def path_default(self, key: str, element: ttk.Entry, default_path: str, save=True, prompt=True):
        # prompt are you sure
        if prompt and not mbox(
            f"Set {up_first_case(key.split('_')[1])} Folder to Default",
            f"Are you sure you want to set {key.split('_')[1]} folder back to default?",
            3,
            self.root,
        ):
            return

        element.configure(state="normal")
        element.delete(0, "end")
        element.insert(0, default_path)
        element.configure(state="readonly")
        if save:
            sj.save_key(key, "auto")

    def clear_export(self):
        if mbox("Clear Export Folder", "Are you sure you want to clear the export folder?", 3, self.root):
            # get all the files in the export folder
            files = os.listdir(sj.cache["dir_export"])
            for file in files:
                os.remove(os.path.join(sj.cache["dir_export"], file))
