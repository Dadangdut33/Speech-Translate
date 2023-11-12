from os import listdir, remove, path
from threading import Thread
from tkinter import ttk, filedialog, Menu, Toplevel, Frame, LabelFrame
from typing import Union
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.combobox import ComboboxWithKeyNav

from loguru import logger

from speech_translate.linker import sj, bc
from speech_translate._path import dir_log, dir_temp, dir_debug
from speech_translate._logging import current_log, change_log_level
from speech_translate.utils.helper import popup_menu, emoji_img, up_first_case
from speech_translate.utils.whisper.download import verify_model_faster_whisper, verify_model_whisper, download_model, get_default_download_root
from speech_translate.utils.helper import start_file
from speech_translate.utils.tk.style import set_ui_style
from speech_translate.ui.custom.message import mbox
from speech_translate.ui.custom.tooltip import tk_tooltip, tk_tooltips


class ModelDownloadFrame:
    def __init__(self, master, model_name, btn_cb) -> None:
        self.f = ttk.Frame(master)
        self.f.pack(side="left", fill="x", padx=5, pady=5)

        self.lf_model = ttk.LabelFrame(self.f, text=model_name)
        self.lf_model.pack(side="left")

        self.btn = ttk.Button(self.lf_model, text="Verify", command=btn_cb)
        self.btn.pack(side="left", padx=5, pady=5)


class SettingGeneral:
    """
    General tab in setting window.
    """
    def __init__(self, root: Toplevel, master_frame: Union[ttk.Frame, Frame]):
        self.root = root
        self.master = master_frame
        self.initial_theme = ""
        self.checking_model = False
        self.model_checked = False
        self.folder_emoji = emoji_img(13, " 📂")
        self.open_emoji = emoji_img(13, "     ↗️")
        self.trash_emoji = emoji_img(13, "     🗑️")
        self.reset_emoji = emoji_img(13, " 🔄")
        self.wrench_emoji = emoji_img(16, "     🛠️")

        # ------------------ General ------------------
        # app
        self.lf_application = LabelFrame(self.master, text="• Application")
        self.lf_application.pack(side="top", fill="x", padx=5, pady=5)

        self.f_application_1 = ttk.Frame(self.lf_application)
        self.f_application_1.pack(side="top", fill="x", padx=5)

        self.f_application_2 = ttk.Frame(self.lf_application)
        self.f_application_2.pack(side="top", fill="x", padx=5)

        self.f_application_3 = ttk.Frame(self.lf_application)
        self.f_application_3.pack(side="top", fill="x", padx=5)

        self.cbtn_update_on_start = CustomCheckButton(
            self.f_application_1,
            sj.cache["checkUpdateOnStart"],
            lambda x: sj.save_key("checkUpdateOnStart", x),
            text="Check for update on start",
            style="Switch.TCheckbutton"
        )
        self.cbtn_update_on_start.pack(side="left", padx=5, pady=5)

        self.cbtn_supress_hidden_to_tray = CustomCheckButton(
            self.f_application_1,
            sj.cache["supress_hidden_to_tray"],
            lambda x: sj.save_key("supress_hidden_to_tray", x),
            text="Supress hidden to tray notif",
            style="Switch.TCheckbutton"
        )
        self.cbtn_supress_hidden_to_tray.pack(side="left", padx=5, pady=5)

        self.cbtn_supress_device_warning = CustomCheckButton(
            self.f_application_1,
            sj.cache["supress_device_warning"],
            lambda x: sj.save_key("supress_device_warning", x),
            text="Supress device warning",
            style="Switch.TCheckbutton"
        )
        self.cbtn_supress_device_warning.pack(side="left", padx=5, pady=5)
        tk_tooltip(
            self.cbtn_supress_device_warning,
            "Supress warning notification that usually shows up when no input device is detected.",
        )

        self.lbl_notice_theme = ttk.Label(
            self.f_application_1,
            text="— Might need to reload the app for theme changes to fully take effect.",
            cursor="hand2",
            foreground="blue",
        )
        self.lbl_notice_theme.bind("<Button-1>", lambda e: self.prompt_restart_app_after_changing_theme())
        self.lbl_notice_theme.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.lbl_notice_theme, "Click here to reload the app.")

        # theme
        self.lbl_theme = ttk.Label(self.f_application_2, text="Theme")
        self.lbl_theme.pack(side="left", padx=5, pady=5)

        self.cb_theme = ComboboxWithKeyNav(self.f_application_2, values=["dummy list"], state="readonly")
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
            "Add custom theme.\n\nThe theme name should be according to the `set_theme` "
            "parameter in the .tcl folder of the theme."
            "\n\nMight need to reload the app for the changes to take effect.",
            wrapLength=500,
        )

        # --------------------
        # log
        self.lf_logging = LabelFrame(self.master, text="• Logging")
        self.lf_logging.pack(side="top", fill="x", padx=5, pady=5)

        self.f_logging_1 = ttk.Frame(self.lf_logging)
        self.f_logging_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_2 = ttk.Frame(self.lf_logging)
        self.f_logging_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_3 = ttk.Frame(self.lf_logging)
        self.f_logging_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_4 = ttk.Frame(self.lf_logging)
        self.f_logging_4.pack(side="top", fill="x", pady=5, padx=5)

        self.f_logging_5 = ttk.Frame(self.lf_logging)
        self.f_logging_5.pack(side="top", fill="x", pady=5, padx=5)

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

        # self.lbl_ignore_stdout = ttk.Label(self.f_logging_2, text="Ignore stdout", width=16)
        # self.lbl_ignore_stdout.pack(side="left", padx=5)
        # tk_tooltip(self.lbl_ignore_stdout, "Collection to ignore stdout / print from the console.")
        # self.entry_ignore_stdout = ttk.Entry(self.f_logging_2)
        # self.entry_ignore_stdout.pack(side="left", padx=5, fill="x", expand=True)
        # self.entry_ignore_stdout.insert(0, ', '.join(sj.cache["ignore_stdout"]))
        # self.entry_ignore_stdout.bind("<FocusOut>", lambda e: self.save_ignore_stdout())
        # self.entry_ignore_stdout.bind("<Return>", lambda e: self.save_ignore_stdout())
        # tk_tooltip(
        #     self.entry_ignore_stdout,
        #     "Collection to ignore stdout / print from the console with its input separated by comma.\n\n"
        #     "This is useful if you want to ignore some of the stdout / print from the console.\n\n"
        #     "Example: `Predicting silences(s) with VAD..., Predicted silences(s) with VAD`",
        #     wrapLength=500,
        # )

        self.menu_config_log = Menu(self.master, tearoff=0)
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

        self.cbtn_verbose = CustomCheckButton(
            self.f_logging_3,
            sj.cache["verbose"],
            lambda x: sj.save_key("verbose", x),
            text="Verbose logging for whisper",
            style="Switch.TCheckbutton"
        )
        self.cbtn_verbose.pack(side="left", padx=5)

        self.cbtn_keep_log = CustomCheckButton(
            self.f_logging_4,
            sj.cache["keep_log"],
            lambda x: sj.save_key("keep_log", x),
            text="Keep log files",
            style="Switch.TCheckbutton"
        )
        self.cbtn_keep_log.pack(side="left", padx=5)

        self.lbl_loglevel = ttk.Label(self.f_logging_4, text="— Log level")
        self.lbl_loglevel.pack(side="left", padx=(0, 5))

        self.cb_log_level = ComboboxWithKeyNav(
            self.f_logging_4, values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], state="readonly"
        )
        self.cb_log_level.pack(side="left", padx=0)
        self.cb_log_level.set(sj.cache["log_level"])
        self.cb_log_level.bind("<<ComboboxSelected>>", self.log_level_change)

        self.cbtn_debug_realtime_record = CustomCheckButton(
            self.f_logging_5,
            sj.cache["debug_realtime_record"],
            lambda x: sj.save_key("debug_realtime_record", x),
            text="Debug recording",
            style="Switch.TCheckbutton"
        )
        self.cbtn_debug_realtime_record.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_debug_realtime_record,
            "Show some debugging process of the realtime record.\n\n"
            "Enabling will probably slow down the app.",
        )

        self.cbtn_debug_recorded_audio = CustomCheckButton(
            self.f_logging_5,
            sj.cache["debug_recorded_audio"],
            lambda x: sj.save_key("debug_recorded_audio", x),
            text="Debug recorded audio",
            style="Switch.TCheckbutton"
        )
        self.cbtn_debug_recorded_audio.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_debug_recorded_audio,
            "Save recorded audio as .wav file in the debug folder. "
            "Keep in mind that the files in that directory will be deleted automatically every time the app run\n\n"
            "Enabling Could slow the app down.",
            wrapLength=300,
        )

        self.cbtn_debug_translate = CustomCheckButton(
            self.f_logging_5,
            sj.cache["debug_translate"],
            lambda x: sj.save_key("debug_translate", x),
            text="Debug translate",
            style="Switch.TCheckbutton"
        )
        self.cbtn_debug_translate.pack(side="left", padx=5, pady=(0, 5))

        # model
        self.ft1lf_model = LabelFrame(self.master, text="• Model")
        self.ft1lf_model.pack(side="top", fill="x", padx=5, pady=5)

        # label model location
        self.f_model_1 = ttk.Frame(self.ft1lf_model)
        self.f_model_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_model_2 = ttk.Frame(self.ft1lf_model)
        self.f_model_2.pack(side="top", fill="x", pady=0, padx=5)

        self.lf_model_whisper = ttk.LabelFrame(self.ft1lf_model, text="Whisper Model")
        self.lf_model_whisper.pack(side="top", fill="x", padx=5, pady=5)

        self.f_mod_whisper = ttk.Frame(self.lf_model_whisper)
        self.f_mod_whisper.pack(side="top", fill="x", padx=5, pady=(0, 5))

        self.lf_model_faster_whisper = ttk.LabelFrame(self.ft1lf_model, text="Faster Whisper Model")
        self.lf_model_faster_whisper.pack(side="top", fill="x", padx=5, pady=5)

        self.f_mod_faster = ttk.Frame(self.lf_model_faster_whisper)
        self.f_mod_faster.pack(side="top", fill="x", padx=5, pady=(0, 5))

        self.lbl_model = ttk.Label(self.f_model_1, text="Model Directory ", width=16)
        self.lbl_model.pack(side="left", padx=5)

        self.entry_model = ttk.Entry(self.f_model_1, cursor="hand2", width=100)
        self.entry_model.pack(side="left", padx=5, fill="x", expand=True)
        tk_tooltip(self.entry_model, "Location of the model file.")

        self.cbtn_auto_verify_model_on_first_setting_open = CustomCheckButton(
            self.f_model_2,
            sj.cache["auto_verify_model_on_first_setting_open"],
            lambda x: sj.save_key("auto_verify_model_on_first_setting_open", x),
            text="Auto check model on start",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_verify_model_on_first_setting_open.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_verify_model_on_first_setting_open,
            "Check if model is downloaded on first setting open.\n\n"
            "If you have a lot of model downloaded, this could take a while and might use RAM depending on the model size.",
        )

        self.btn_model_config = ttk.Button(
            self.f_model_1,
            image=self.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_config_model),
        )
        self.btn_model_config.pack(side="left", padx=5, pady=5)

        self.menu_config_model = Menu(self.master, tearoff=0)
        self.menu_config_model.add_command(
            label="Open",
            image=self.open_emoji,
            compound="left",
            command=lambda:
            start_file(sj.cache["dir_model"] if sj.cache["dir_model"] != "auto" else get_default_download_root())
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

        self.model_tiny = ModelDownloadFrame(
            self.f_mod_whisper, "Tiny", lambda: self.model_btn_checker("tiny", self.model_tiny.btn)
        )
        self.model_tiny_eng = ModelDownloadFrame(
            self.f_mod_whisper, "Tiny (en)", lambda: self.model_btn_checker("tiny.en", self.model_tiny_eng.btn)
        )
        self.model_base = ModelDownloadFrame(
            self.f_mod_whisper, "Base", lambda: self.model_btn_checker("base", self.model_base.btn)
        )
        self.model_base_eng = ModelDownloadFrame(
            self.f_mod_whisper, "Base (en)", lambda: self.model_btn_checker("base.en", self.model_base_eng.btn)
        )
        self.model_small = ModelDownloadFrame(
            self.f_mod_whisper, "Small", lambda: self.model_btn_checker("small", self.model_small.btn)
        )
        self.model_small_eng = ModelDownloadFrame(
            self.f_mod_whisper, "Small (en)", lambda: self.model_btn_checker("small.en", self.model_small_eng.btn)
        )
        self.model_medium = ModelDownloadFrame(
            self.f_mod_whisper, "Medium", lambda: self.model_btn_checker("medium", self.model_medium.btn)
        )
        self.model_medium_eng = ModelDownloadFrame(
            self.f_mod_whisper, "Medium (en)", lambda: self.model_btn_checker("medium.en", self.model_medium_eng.btn)
        )
        self.model_large_v1 = ModelDownloadFrame(
            self.f_mod_whisper, "Large (v1)", lambda: self.model_btn_checker("large-v1", self.model_large_v1.btn)
        )
        self.model_large_v2 = ModelDownloadFrame(
            self.f_mod_whisper, "Large (v2)", lambda: self.model_btn_checker("large-v2", self.model_large_v2.btn)
        )
        self.model_large_v3 = ModelDownloadFrame(
            self.f_mod_whisper, "Large (v3)", lambda: self.model_btn_checker("large-v3", self.model_large_v3.btn)
        )

        self.model_faster_tiny = ModelDownloadFrame(
            self.f_mod_faster, "Tiny", lambda: self.model_btn_checker("tiny", self.model_faster_tiny.btn, True)
        )

        self.model_faster_tiny_eng = ModelDownloadFrame(
            self.f_mod_faster, "Tiny (en)", lambda: self.model_btn_checker("tiny.en", self.model_faster_tiny_eng.btn, True)
        )

        self.model_faster_base = ModelDownloadFrame(
            self.f_mod_faster, "Base", lambda: self.model_btn_checker("base", self.model_faster_base.btn, True)
        )

        self.model_faster_base_eng = ModelDownloadFrame(
            self.f_mod_faster, "Base (en)", lambda: self.model_btn_checker("base.en", self.model_faster_base_eng.btn, True)
        )

        self.model_faster_small = ModelDownloadFrame(
            self.f_mod_faster, "Small", lambda: self.model_btn_checker("small", self.model_faster_small.btn, True)
        )

        self.model_faster_small_eng = ModelDownloadFrame(
            self.f_mod_faster, "Small (en)",
            lambda: self.model_btn_checker("small.en", self.model_faster_small_eng.btn, True)
        )

        self.model_faster_medium = ModelDownloadFrame(
            self.f_mod_faster, "Medium", lambda: self.model_btn_checker("medium", self.model_faster_medium.btn, True)
        )

        self.model_faster_medium_eng = ModelDownloadFrame(
            self.f_mod_faster, "Medium (en)",
            lambda: self.model_btn_checker("medium.en", self.model_faster_medium_eng.btn, True)
        )

        self.model_faster_large_v1 = ModelDownloadFrame(
            self.f_mod_faster, "Large (v1)",
            lambda: self.model_btn_checker("large-v1", self.model_faster_large_v1.btn, True)
        )

        self.model_faster_large_v2 = ModelDownloadFrame(
            self.f_mod_faster, "Large (v2)",
            lambda: self.model_btn_checker("large-v2", self.model_faster_large_v2.btn, True)
        )
        # self.model_faster_large_v3 = ModelDownloadFrame(
        #     self.f_mod_faster, "Large (v3)",
        #     lambda: self.model_btn_checker("large-v3", self.model_faster_large_v3.btn, True)
        # )

        # ------------------ Functions ------------------
        self.init_setting_once()

    # ------------------ Functions ------------------
    def init_setting_once(self):
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

        self.fill_theme()

    def delete_log(self):
        # delete all log files
        for file in listdir(dir_log):
            if file.endswith(".log"):
                try:
                    remove(path.join(dir_log, file))
                except Exception as e:
                    if file != current_log:  # show warning only if the fail to delete is not the current log
                        logger.warning("Failed to delete log file: " + file)
                        logger.warning("Reason " + str(e))

    def delete_temp(self):
        # delete all temp wav files
        for file in listdir(dir_temp):
            if file.endswith(".wav"):
                try:
                    remove(path.join(dir_temp, file))
                except Exception as e:
                    logger.warning("Failed to delete temp file: " + file)
                    logger.warning("Reason " + str(e))

    def delete_debug(self):
        # delete all debug files
        for file in listdir(dir_debug):
            try:
                remove(path.join(dir_debug, file))
            except Exception as e:
                logger.warning("Failed to delete debug file: " + file)
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

    def model_download(self, model: str, btn: ttk.Button, use_faster_whisper: bool) -> None:
        # if already downloading then return
        if bc.dl_thread and bc.dl_thread.is_alive():
            mbox("Already downloading", "Please wait for the current download to finish.", 0, self.root)
            return

        # confirmation using mbox
        if not mbox("Download confirmation", f"Are you sure you want to download {model} model?", 3, self.root):
            return

        def after_func():
            btn.configure(text="Downloaded", state="disabled")

        kwargs = {
            "after_func": after_func,
            "use_faster_whisper": use_faster_whisper,
            "cancel_func": lambda: self.cancel_model_download(model, btn)
        }

        # verify first
        if sj.cache["dir_model"] != "auto":
            kwargs["download_root"] = sj.cache["dir_model"],

        if not use_faster_whisper:
            if verify_model_whisper(model):  # already downloaded
                after_func()
                return

        # Download model
        try:
            bc.dl_thread = Thread(
                target=download_model,
                args=(model, self.root),
                daemon=True,
                kwargs=kwargs,
            )
            bc.dl_thread.start()

            btn.configure(text="Downloading...", state="disabled")
        except Exception as e:
            btn.configure(
                text="Download", command=lambda: self.model_download(model, btn, use_faster_whisper), state="normal"
            )
            mbox("Download error", f"Err details: {e}", 0, self.root)

    def cancel_model_download(self, model: str, btn: ttk.Button) -> None:
        """
        Cancel whisper model download.

        Faster whisper download is not cancellable.
        """
        if not mbox("Cancel confirmation", "Are you sure you want to cancel downloading?", 3, self.root):
            return

        btn.configure(text="Download", command=lambda: self.model_download(model, btn, False), state="normal")
        bc.cancel_dl = True  # Raise flag to stop

    def model_btn_checker(self, model: str, btn: ttk.Button, faster_whisper: bool = False) -> None:
        """
        Helper to check if model is downloaded.
        It will first change btn state to disabled to prevent user from clicking it, set text to "Checking..."
        Then check it and change the text and state accordingly.
        """
        # if button already says downloaded or download then return because it means it is already checked
        if btn["text"] in ["Downloaded", "Download"]:
            return

        btn.configure(text="Checking...", state="disabled")

        model_dir = sj.cache["dir_model"] if sj.cache["dir_model"] != "auto" else get_default_download_root()
        if faster_whisper:
            downloaded = verify_model_faster_whisper(model, model_dir)
        else:
            downloaded = verify_model_whisper(model, model_dir)

        if downloaded:
            btn.configure(text="Downloaded", state="disabled")
        else:
            btn.configure(text="Download", command=lambda: self.model_download(model, btn, faster_whisper), state="normal")

    def check_model_on_first_open(self):
        """
        Check if model is downloaded on first setting open.
        It need to be checked hardcodedly because for some reason 
        if i try to use a map it keep referencing to the wrong button.
        """
        self.checking_model = True
        try:

            def threaded_tiny_w():
                try:
                    self.model_btn_checker("tiny", self.model_tiny.btn)
                    self.model_btn_checker("tiny.en", self.model_tiny_eng.btn)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_tiny_fw():
                try:
                    self.model_btn_checker("tiny", self.model_faster_tiny.btn, True)
                    self.model_btn_checker("tiny.en", self.model_faster_tiny_eng.btn, True)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_base_w():
                try:
                    self.model_btn_checker("base", self.model_base.btn)
                    self.model_btn_checker("base.en", self.model_base_eng.btn)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_base_fw():
                try:
                    self.model_btn_checker("base", self.model_faster_base.btn, True)
                    self.model_btn_checker("base.en", self.model_faster_base_eng.btn, True)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_small_w():
                try:
                    self.model_btn_checker("small", self.model_small.btn)
                    self.model_btn_checker("small.en", self.model_small_eng.btn)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_small_fw():
                try:
                    self.model_btn_checker("small", self.model_faster_small.btn, True)
                    self.model_btn_checker("small.en", self.model_faster_small_eng.btn, True)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_medium_w():
                try:
                    self.model_btn_checker("medium", self.model_medium.btn)
                    self.model_btn_checker("medium.en", self.model_medium_eng.btn)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_medium_fw():
                try:
                    self.model_btn_checker("medium", self.model_faster_medium.btn, True)
                    self.model_btn_checker("medium.en", self.model_faster_medium_eng.btn, True)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_large_v1_w():
                try:
                    self.model_btn_checker("large-v1", self.model_large_v1.btn)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_large_v1_fw():
                try:
                    self.model_btn_checker("large-v1", self.model_faster_large_v1.btn, True)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_large_v2_w():
                try:
                    self.model_btn_checker("large-v2", self.model_large_v2.btn)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_large_v2_fw():
                try:
                    self.model_btn_checker("large-v2", self.model_faster_large_v2.btn, True)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            def threaded_large_v3():
                try:
                    self.model_btn_checker("large-v3", self.model_large_v3.btn)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

            # def threaded_large_v3_fw():
            #     try:
            #         self.model_btn_checker("large-v3", self.model_faster_large_v3.btn, True)
            #     except Exception as e:
            #         if "invalid command name" not in str(e):
            #             logger.exception(e)

            check_tiny_w = Thread(target=threaded_tiny_w, daemon=True)
            check_tiny_fw = Thread(target=threaded_tiny_fw, daemon=True)
            check_base_w = Thread(target=threaded_base_w, daemon=True)
            check_base_fw = Thread(target=threaded_base_fw, daemon=True)
            check_small_w = Thread(target=threaded_small_w, daemon=True)
            check_small_fw = Thread(target=threaded_small_fw, daemon=True)
            check_medium_w = Thread(target=threaded_medium_w, daemon=True)
            check_medium_fw = Thread(target=threaded_medium_fw, daemon=True)
            check_large_v1_w = Thread(target=threaded_large_v1_w, daemon=True)
            check_large_v1_fw = Thread(target=threaded_large_v1_fw, daemon=True)
            check_large_v2_w = Thread(target=threaded_large_v2_w, daemon=True)
            check_large_v2_fw = Thread(target=threaded_large_v2_fw, daemon=True)
            check_large_v3_w = Thread(target=threaded_large_v3, daemon=True)
            # check_large_v3_fw = Thread(target=threaded_large_v3_fw, daemon=True)

            check_tiny_w.start()
            check_tiny_w.join()
            check_tiny_fw.start()
            check_tiny_fw.join()

            check_base_w.start()
            check_base_w.join()
            check_base_fw.start()
            check_base_fw.join()

            check_small_w.start()
            check_small_w.join()
            check_small_fw.start()
            check_small_fw.join()

            check_medium_w.start()
            check_medium_w.join()
            check_medium_fw.start()
            check_medium_fw.join()

            check_large_v1_w.start()
            check_large_v1_w.join()
            check_large_v1_fw.start()
            check_large_v1_fw.join()

            check_large_v2_w.start()
            check_large_v2_w.join()
            check_large_v2_fw.start()
            check_large_v2_fw.join()

            check_large_v3_w.start()
            # check_large_v3_fw.start()
            check_large_v3_w.join()
            # check_large_v3_fw.join()

            self.model_checked = True
        except Exception as e:
            logger.error("Failed to check model on first setting open")
            logger.exception(e)
        finally:
            self.checking_model = False

    def fill_theme(self):
        self.cb_theme["values"] = bc.theme_lists
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
            assert bc.mw is not None
            bc.mw.restart_app()

    def cb_theme_change(self, _event=None):
        if self.cb_theme.get() == "custom":
            self.entry_theme.pack(side="left", padx=5, pady=5, fill="x", expand=True)
            self.entry_theme.delete(0, "end")
            self.btn_theme_add.pack(side="left", padx=5, pady=5)
        else:
            prev = sj.cache["theme"]
            # check if the theme is the same as the previous one
            if prev == self.cb_theme.get():
                return

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

        if theme_name in bc.theme_lists:
            mbox("Error", "Theme name already exist", 0, self.root)
            return

        if set_ui_style(theme_name, self.root):
            # add the theme to the list
            bc.theme_lists.append(theme_name)

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
        change_log_level(self.cb_log_level.get())

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

    # def save_ignore_stdout(self):
    #     _input = self.entry_ignore_stdout.get().split(",")
    #     _input = [i.strip() for i in _input if i.strip() != ""]  # remove any empty string or space

    #     sj.save_key("ignore_stdout", _input)
    #     update_stdout_ignore_list(_input)
