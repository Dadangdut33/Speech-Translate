import threading
import random
import tkinter as tk
from tkinter import ttk, font

from speech_translate._path import app_icon
from speech_translate._contants import APP_NAME, PREVIEW_WORDS
from speech_translate.globals import sj, gc
from speech_translate.utils.helper import chooseColor
from speech_translate.utils.helper import cbtn_invoker
from speech_translate.utils.helper_whisper import convert_str_options_to_dict, get_temperature

from speech_translate.components.frame.setting_general import SettingGeneral
from speech_translate.components.frame.setting_record import SettingRecord

from speech_translate.components.custom.message import mbox, MBoxText
from speech_translate.components.custom.tooltip import tk_tooltip, tk_tooltip, CreateToolTipOnText, tk_tooltips


# TODO: proxies, whisper option


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

        self.ft_record = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft_record, text="Record")
        self.ft_record.bind("<Button-1>", lambda event: self.root.focus_set())

        self.ft_transcribe = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft_transcribe, text="Transcribe")
        self.ft_transcribe.bind("<Button-1>", lambda event: self.root.focus_set())

        self.ft_translate = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft_translate, text="Translate")
        self.ft_translate.bind("<Button-1>", lambda event: self.root.focus_set())

        self.ft_textbox = ttk.Frame(self.tabControl)
        self.tabControl.add(self.ft_textbox, text="Textbox")
        self.ft_textbox.bind("<Button-1>", lambda event: self.root.focus_set())

        # Insert the frames
        self.f_general = SettingGeneral(self.root, self.ft_general)
        self.f_record = SettingRecord(self.root, self.ft_record)

        # ------------------ Transcribe  ------------------
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

        #! move this to transcribe
        self.lbl_tc_rate = ttk.Label(self.f_tc_params_1, text="Transcribe Rate (ms)", width=18)
        self.lbl_tc_rate.pack(side="left", padx=5)
        self.spn_tc_rate = ttk.Spinbox(
            self.f_tc_params_1,
            from_=1,
            to=1000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.save_key("transcribe_rate", int(self.spn_tc_rate.get())),
        )
        self.spn_tc_rate.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(
                self.spn_tc_rate, 1, 1000, lambda: sj.save_key("transcribe_rate", int(self.spn_tc_rate.get()))
            ),
        )
        self.spn_tc_rate.pack(side="left", padx=5)
        tk_tooltips(
            [self.spn_tc_rate, self.lbl_tc_rate],
            "Set the transcribe rate or the time between each transcribe check. \n\nFor more real time experience you can lower it more. The lower the value, the more resource it will use.\n\nIf you lower the transcribe rate, you should also lower the max buffer for a better experience.\n\nDefault value is 300ms.",
            wrapLength=350,
        )

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
            command=lambda: sj.save_key(
                "condition_on_previous_text", self.cbtn_condition_on_previous_text.instate(["selected"])
            ),
            style="Switch.TCheckbutton",
        )
        self.cbtn_condition_on_previous_text.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_condition_on_previous_text,
            """if True, the previous output of the model is provided as a prompt for the next window;
        \rDisabling may make the text inconsistent across windows, but the model becomes less prone to getting stuck in a failure loop, such as repetition looping or timestamps going out of sync.
        \rDefault value is true/checked""",
        )

        self.lbl_compression_ratio_threshold = ttk.Label(self.f_extra_whisper_args_2, text="Compression threshold", width=21)
        self.lbl_compression_ratio_threshold.pack(side="left", padx=5)

        self.spn_compression_ratio_threshold = ttk.Spinbox(
            self.f_extra_whisper_args_2,
            format="%.2f",
            from_=-100,
            to=100,
            increment=0.1,
            validate="key",
            validatecommand=(self.root.register(self.number_only_float), "%P"),
            command=lambda: sj.save_key("compression_ratio_threshold", float(self.spn_compression_ratio_threshold.get())),
        )
        self.spn_compression_ratio_threshold.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber_float(
                self.spn_compression_ratio_threshold,
                -100,
                100,
                lambda: sj.save_key("compression_ratio_threshold", float(self.spn_compression_ratio_threshold.get())),
            ),
        )
        self.spn_compression_ratio_threshold.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_compression_ratio_threshold, self.spn_compression_ratio_threshold],
            "Compression ratio threshold.\n\nIf the gzip compression ratio is above this value, treat as failed.\n\nDefault value is 2.4",
        )

        self.lbl_logprob_threshold = ttk.Label(self.f_extra_whisper_args_2, text="Logprob threshold", width=21)
        self.lbl_logprob_threshold.pack(side="left", padx=5)

        self.spn_logprob_threshold = ttk.Spinbox(
            self.f_extra_whisper_args_2,
            format="%.2f",
            from_=-100,
            to=100,
            increment=0.1,
            validate="key",
            validatecommand=(self.root.register(self.number_only_float), "%P"),
            command=lambda: sj.save_key("logprob_threshold", float(self.spn_logprob_threshold.get())),
        )
        self.spn_logprob_threshold.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber_float(
                self.spn_logprob_threshold,
                -100,
                100,
                lambda: sj.save_key("logprob_threshold", float(self.spn_logprob_threshold.get())),
            ),
        )
        self.spn_logprob_threshold.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_logprob_threshold, self.spn_logprob_threshold],
            "If the average log probability over sampled tokens is below this value, treat as failed.\n\nDefault value is -1.0",
        )

        self.lbl_no_speech_threshold = ttk.Label(self.f_extra_whisper_args_2, text="No speech threshold", width=21)
        self.lbl_no_speech_threshold.pack(side="left", padx=5)

        self.spn_no_speech_threshold = ttk.Spinbox(
            self.f_extra_whisper_args_2,
            format="%.2f",
            from_=-100,
            to=100,
            increment=0.1,
            validatecommand=(self.root.register(self.number_only_float), "%P"),
            command=lambda: sj.save_key("no_speech_threshold", float(self.spn_no_speech_threshold.get())),
        )
        self.spn_no_speech_threshold.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber_float(
                self.spn_no_speech_threshold,
                -100,
                100,
                lambda: sj.save_key("no_speech_threshold", float(self.spn_no_speech_threshold.get())),
            ),
        )
        self.spn_no_speech_threshold.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_no_speech_threshold, self.spn_no_speech_threshold],
            """If the no_speech probability is higher than this value AND the average log probability
        \rover sampled tokens is below `logprob_threshold`, consider the segment as silent.\n\nDefault value is 0.6""",
        )

        self.lbl_initial_prompt = ttk.Label(self.f_extra_whisper_args_3, text="Initial prompt", width=21)
        self.lbl_initial_prompt.pack(side="left", padx=5)

        self.entry_initial_prompt = ttk.Entry(self.f_extra_whisper_args_3)
        self.entry_initial_prompt.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_initial_prompt.bind(
            "<KeyRelease>", lambda e: sj.save_key("initial_prompt", self.entry_initial_prompt.get())
        )
        tk_tooltips(
            [self.lbl_initial_prompt, self.entry_initial_prompt],
            "optional text to provide as a prompt for the first window.\n\nDefault is empty",
        )

        self.lbl_temperature = ttk.Label(self.f_extra_whisper_args_3, text="Temperature", width=18)
        self.lbl_temperature.pack(side="left", padx=5)

        self.entry_temperature = ttk.Entry(self.f_extra_whisper_args_3)
        self.entry_temperature.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_temperature.bind("<KeyRelease>", lambda e: sj.save_key("temperature", self.entry_temperature.get()))
        tk_tooltips(
            [self.lbl_temperature, self.entry_temperature],
            "Temperature for sampling. It can be a tuple of temperatures, which will be successively used upon failures according to either `compression_ratio_threshold` or `logprob_threshold`.\n\nDefault is 0.0, 0.2, 0.4, 0.6, 0.8, 1.0",
        )

        self.btn_verify_temperature = ttk.Button(
            self.f_extra_whisper_args_3, text="Verify", command=lambda: self.verifyTemp()
        )
        self.btn_verify_temperature.pack(side="left", padx=5)
        tk_tooltip(self.btn_verify_temperature, "Verify temperature input.")

        rng = random.randint(0, 10000)
        self.lbl_extra_whisper_args = ttk.Label(self.f_extra_whisper_args_4, text="Extra parameter", width=21)
        self.lbl_extra_whisper_args.pack(side="left", padx=5)

        self.entry_whisper_extra_args = ttk.Entry(self.f_extra_whisper_args_4)
        self.entry_whisper_extra_args.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_whisper_extra_args.bind(
            "<KeyRelease>", lambda e: sj.save_key("whisper_extra_args", self.entry_whisper_extra_args.get())
        )
        tk_tooltip(self.entry_whisper_extra_args, "Whisper extra arguments.\n\nDefault is empty")

        hint = (
            "Extra arguments to pass to the whisper command. Default value is empty / using whisper default"
            "\n(Usage value shown as example here are only for reference)"
            #
            "\n\n# Maximum number of tokens to sample"
            "\nsample_len: int\n--sample_len 0"
            #
            "\n\n# Number of independent samples to collect, when t > 0"
            "\nbest_of: int\n--best_of 0"
            #
            "\n\n# Number of beams in beam search, when t == 0"
            "\nbeam_size: int\n--beam_size 0"
            #
            "\n\n# Patience in beam search (https://arxiv.org/abs/2204.05424)"
            "\npatience: float\n--patience 0.0"
            #
            "\n\n# Options for ranking generations (either beams or best-of-N samples)"
            "\n# 'alpha' in Google NMT, None defaults to length norm"
            "\nlength_penalty: float = None\n--length_penalty 0.0"
            #
            "\n\n# Text or tokens for the previous context"
            f'\nprompt: str or [int]\n--prompt "hello world" or --prompt [1, 2, 3]'
            #
            "\n\n# Text or tokens to prefix the current context"
            f'\nprefix: str or [int]\n--prefix "hello world" or --prefix [1, 2, 3]'
            #
            "\n\n# Text or tokens for the previous context"
            "\nsuppress_blank: bool\n--suppress_blank true"
            #
            f'\n\n# List of tokens ids (or comma-separated token ids) to suppress\n# "-1" will suppress a set of symbols as defined in `tokenizer.non_speech_tokens()`'
            f'\nsuppress_tokens: str or [int]\n--suppress_tokens "-1" or --suppress_tokens [-1, 0]'
            #
            "\n\n# Timestamp sampling options"
            "\nwithout_timestamps: bool\n--without_timestamps true"
            #
            "\n\n# The initial timestamp cannot be later than this"
            "\nmax_initial_timestamp: float\n--max_initial_timestamp 1.0"
            #
            "\n\n# Implementation details"
            "\n# Use fp16 for most of the calculation"
            "\nfp16: bool\n--fp16 true"
        )
        CreateToolTipOnText(self.entry_whisper_extra_args, hint, geometry="700x250")

        self.btn_help = ttk.Button(
            self.f_extra_whisper_args_4,
            text="❔",
            command=lambda: MBoxText("whisper-params", self.root, "Whisper Args", hint),
            width=5,
        )
        self.btn_help.pack(side="left", padx=5)
        tk_tooltip(self.btn_help, "Click to see the available arguments.")

        self.btn_verify = ttk.Button(self.f_extra_whisper_args_4, text="Verify", command=lambda: self.verifyWhisperArgs())
        self.btn_verify.pack(side="left", padx=5)
        tk_tooltip(self.btn_verify, "Verify the extra arguments.")

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
        self.entry_libre_key.bind("<KeyRelease>", lambda e: sj.save_key("libre_api_key", self.entry_libre_key.get()))
        tk_tooltips(
            [self.lbl_libre_key, self.entry_libre_key],
            "Libre Translate API Key. Leave empty if not needed or host locally.",
        )

        self.lbl_libre_host = ttk.Label(self.f_libre_1, text="Host")
        self.lbl_libre_host.pack(side="left", padx=5, pady=5)

        self.entry_libre_host = ttk.Entry(self.f_libre_1, width=40)
        self.entry_libre_host.pack(side="left", padx=5, pady=5)
        self.entry_libre_host.bind("<KeyRelease>", lambda e: sj.save_key("libre_host", self.entry_libre_host.get()))
        tk_tooltips(
            [self.lbl_libre_host, self.entry_libre_host],
            "The host of Libre Translate. You can check out the official instance/mirrors at https://github.com/LibreTranslate/LibreTranslate or host your own instance",
            wrapLength=300,
        )

        self.lbl_libre_port = ttk.Label(self.f_libre_1, text="Port")
        self.lbl_libre_port.pack(side="left", padx=5, pady=5)
        self.lbl_libre_port.bind("<KeyRelease>", lambda e: sj.save_key("libre_port", self.entry_libre_port.get()))

        self.entry_libre_port = ttk.Entry(self.f_libre_1)
        self.entry_libre_port.pack(side="left", padx=5, pady=5)
        self.entry_libre_port.bind("<KeyRelease>", lambda e: sj.save_key("libre_port", self.entry_libre_port.get()))
        tk_tooltips([self.lbl_libre_port, self.entry_libre_port], "Libre Translate Port.")

        self.cbtn_libre_https = ttk.Checkbutton(
            self.f_libre_1,
            text="Use HTTPS",
            command=lambda: sj.save_key("libre_https", self.cbtn_libre_https.instate(["selected"])),
            style="Switch.TCheckbutton",
        )
        self.cbtn_libre_https.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.cbtn_libre_https, "Set it to false if you're hosting locally.")

        # ------------------ Textbox ------------------
        self.f_textbox = ttk.Frame(self.ft_textbox)
        self.f_textbox.pack(side="top", fill="both", padx=5, pady=5, expand=False)

        # mw tc
        self.lf_mw_tc = tk.LabelFrame(self.f_textbox, text="• Main Window Transcribed Speech")
        self.lf_mw_tc.pack(side="top", padx=5, pady=5, fill="x", expand=True)

        self.lbl_mw_tc_max = ttk.Label(self.lf_mw_tc, text="Max Length")
        self.lbl_mw_tc_max.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.lbl_mw_tc_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.spn_mw_tc_max = ttk.Spinbox(
            self.lf_mw_tc,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.save_key("tb_mw_tc_max", int(self.spn_mw_tc_max.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_mw_tc_max.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(
                self.spn_mw_tc_max,
                0,
                5000,
                lambda: sj.save_key("tb_mw_tc_max", int(self.spn_mw_tc_max.get())),
            )
            or self.preview_changes_tb(),
        )
        self.spn_mw_tc_max.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.spn_mw_tc_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.lbl_mw_tc_font = ttk.Label(self.lf_mw_tc, text="Font")
        self.lbl_mw_tc_font.pack(side="left", padx=5, pady=5)

        self.cb_mw_tc_font = ttk.Combobox(self.lf_mw_tc, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tc_font.pack(side="left", padx=5, pady=5)
        self.cb_mw_tc_font.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key("tb_mw_tc_font", self.cb_mw_tc_font.get()) or self.preview_changes_tb(),
        )

        self.lbl_mw_tc_font_size = ttk.Label(self.lf_mw_tc, text="Font Size")
        self.lbl_mw_tc_font_size.pack(side="left", padx=5, pady=5)

        self.spn_mw_tc_font_size = ttk.Spinbox(
            self.lf_mw_tc,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.save_key("tb_mw_tc_font_size", int(self.spn_mw_tc_font_size.get()))
            or self.preview_changes_tb(),
            width=10,
        )
        self.spn_mw_tc_font_size.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(
                self.spn_mw_tc_font_size,
                3,
                120,
                lambda: sj.save_key("tb_mw_tc_font_size", int(self.spn_mw_tc_font_size.get())),
            )
            or self.preview_changes_tb(),
        )
        self.spn_mw_tc_font_size.pack(side="left", padx=5, pady=5)

        self.cbtn_mw_tc_font_bold = ttk.Checkbutton(
            self.lf_mw_tc,
            text="Bold",
            command=lambda: sj.save_key("tb_mw_tc_font_bold", self.cbtn_mw_tc_font_bold.instate(["selected"]))
            or self.preview_changes_tb(),
        )
        self.cbtn_mw_tc_font_bold.pack(side="left", padx=5, pady=5)

        # mw tl
        self.lf_mw_tl = tk.LabelFrame(self.f_textbox, text="• Main Window Translated Speech")
        self.lf_mw_tl.pack(side="top", padx=5, pady=5, fill="x", expand=True)

        self.lbl_mw_tl_max = ttk.Label(self.lf_mw_tl, text="Max Length")
        self.lbl_mw_tl_max.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.lbl_mw_tl_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.spn_mw_tl_max = ttk.Spinbox(
            self.lf_mw_tl,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.save_key("tb_mw_tl_max", int(self.spn_mw_tl_max.get()) or self.preview_changes_tb()),
            width=10,
        )
        self.spn_mw_tl_max.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(
                self.spn_mw_tl_max,
                0,
                5000,
                lambda: sj.save_key("tb_mw_tl_max", int(self.spn_mw_tl_max.get())) or self.preview_changes_tb(),
            ),
        )
        self.spn_mw_tl_max.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.spn_mw_tl_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.lbl_mw_tl_font = ttk.Label(self.lf_mw_tl, text="Font")
        self.lbl_mw_tl_font.pack(side="left", padx=5, pady=5)

        self.cb_mw_tl_font = ttk.Combobox(self.lf_mw_tl, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tl_font.pack(side="left", padx=5, pady=5)
        self.cb_mw_tl_font.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key("tb_mw_tl_font", self.cb_mw_tl_font.get()) or self.preview_changes_tb(),
        )

        self.lbl_mw_tl_font_size = ttk.Label(self.lf_mw_tl, text="Font Size")
        self.lbl_mw_tl_font_size.pack(side="left", padx=5, pady=5)

        self.spn_mw_tl_font_size = ttk.Spinbox(
            self.lf_mw_tl,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.save_key("tb_mw_tl_font_size", int(self.spn_mw_tl_font_size.get()))
            or self.preview_changes_tb(),
            width=10,
        )
        self.spn_mw_tl_font_size.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(
                self.spn_mw_tl_font_size,
                3,
                120,
                lambda: sj.save_key("tb_mw_tl_font_size", int(self.spn_mw_tc_font_size.get())),
            )
            or self.preview_changes_tb(),
        )
        self.spn_mw_tl_font_size.pack(side="left", padx=5, pady=5)

        self.cbtn_mw_tl_font_bold = ttk.Checkbutton(
            self.lf_mw_tl,
            text="Bold",
            command=lambda: sj.save_key("tb_mw_tl_font_bold", self.cbtn_mw_tl_font_bold.instate(["selected"]))
            or self.preview_changes_tb(),
        )
        self.cbtn_mw_tl_font_bold.pack(side="left", padx=5, pady=5)

        # detached tc
        self.lf_ex_tc = tk.LabelFrame(self.f_textbox, text="• Subtitle Window Transcribed Speech")
        self.lf_ex_tc.pack(side="top", padx=5, pady=5, fill="x", expand=True)

        self.lbl_ex_tc_max = ttk.Label(self.lf_ex_tc, text="Max Length")
        self.lbl_ex_tc_max.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.lbl_ex_tc_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.spn_ex_tc_max = ttk.Spinbox(
            self.lf_ex_tc,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.save_key("tb_ex_tc_max", int(self.spn_ex_tc_max.get()) or self.preview_changes_tb()),
            width=10,
        )
        self.spn_ex_tc_max.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(
                self.spn_ex_tc_max,
                0,
                5000,
                lambda: sj.save_key("tb_ex_tc_max", int(self.spn_ex_tc_max.get())) or self.preview_changes_tb(),
            ),
        )
        self.spn_ex_tc_max.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.spn_ex_tc_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.lbl_ex_tc_font = ttk.Label(self.lf_ex_tc, text="Font")
        self.lbl_ex_tc_font.pack(side="left", padx=5, pady=5)

        self.cb_ex_tc_font = ttk.Combobox(self.lf_ex_tc, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tc_font.pack(side="left", padx=5, pady=5)
        self.cb_ex_tc_font.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key("tb_ex_tc_font", self.cb_ex_tc_font.get()) or self.preview_changes_tb(),
        )

        self.lbl_ex_tc_font_size = ttk.Label(self.lf_ex_tc, text="Font Size")
        self.lbl_ex_tc_font_size.pack(side="left", padx=5, pady=5)

        self.spn_ex_tc_font_size = ttk.Spinbox(
            self.lf_ex_tc,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.save_key("tb_ex_tc_font_size", int(self.spn_ex_tc_font_size.get()))
            or self.preview_changes_tb(),
            width=10,
        )
        self.spn_ex_tc_font_size.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(
                self.spn_ex_tc_font_size,
                3,
                120,
                lambda: sj.save_key("tb_ex_tc_font_size", int(self.spn_ex_tc_font_size.get())) or self.preview_changes_tb(),
            ),
        )
        self.spn_ex_tc_font_size.pack(side="left", padx=5, pady=5)

        self.cbtn_ex_tc_font_bold = ttk.Checkbutton(
            self.lf_ex_tc,
            text="Bold",
            command=lambda: sj.save_key("tb_ex_tc_font_bold", self.cbtn_ex_tc_font_bold.instate(["selected"]))
            or self.preview_changes_tb(),
        )
        self.cbtn_ex_tc_font_bold.pack(side="left", padx=5, pady=5)

        self.lbl_ex_tc_font_color = ttk.Label(self.lf_ex_tc, text="Font Color")
        self.lbl_ex_tc_font_color.pack(side="left", padx=5, pady=5)

        self.entry_ex_tc_font_color = ttk.Entry(self.lf_ex_tc, width=10)
        self.entry_ex_tc_font_color.pack(side="left", padx=5, pady=5)
        self.entry_ex_tc_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_font_color, self.entry_ex_tc_font_color.get(), self.root)
            or sj.save_key("tb_ex_tc_font_color", self.entry_ex_tc_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tc_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tc_bg_color = ttk.Label(self.lf_ex_tc, text="Background Color")
        self.lbl_ex_tc_bg_color.pack(side="left", padx=5, pady=5)

        self.entry_ex_tc_bg_color = ttk.Entry(self.lf_ex_tc, width=10)
        self.entry_ex_tc_bg_color.pack(side="left", padx=5, pady=5)
        self.entry_ex_tc_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_bg_color, self.entry_ex_tc_bg_color.get(), self.root)
            or sj.save_key("tb_ex_tc_bg_color", self.entry_ex_tc_bg_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tc_bg_color.bind("<Key>", lambda e: "break")

        # detached tl
        self.lf_ex_tl = tk.LabelFrame(self.f_textbox, text="• Subtitle Window Translated Speech")
        self.lf_ex_tl.pack(side="top", padx=5, pady=5, fill="x", expand=True)

        self.lbl_ex_tl_max = ttk.Label(self.lf_ex_tl, text="Max Length")
        self.lbl_ex_tl_max.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.lbl_ex_tl_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.spn_ex_tl_max = ttk.Spinbox(
            self.lf_ex_tl,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.save_key("tb_ex_tl_max", int(self.spn_ex_tl_max.get())) or self.preview_changes_tb(),
            width=10,
        )
        self.spn_ex_tl_max.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(
                self.spn_ex_tl_max,
                0,
                5000,
                lambda: sj.save_key("tb_ex_tl_max", int(self.spn_ex_tl_max.get())) or self.preview_changes_tb(),
            ),
        )
        self.spn_ex_tl_max.pack(side="left", padx=5, pady=5)
        tk_tooltip(self.spn_ex_tl_max, "Maximum length of the textbox. 0 = no limit.\n\nDefault value is 0.")

        self.lbl_ex_tl_font = ttk.Label(self.lf_ex_tl, text="Font")
        self.lbl_ex_tl_font.pack(side="left", padx=5, pady=5)

        self.cb_ex_tl_font = ttk.Combobox(self.lf_ex_tl, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tl_font.pack(side="left", padx=5, pady=5)
        self.cb_ex_tl_font.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key("tb_ex_tl_font", self.cb_ex_tl_font.get()) or self.preview_changes_tb(),
        )

        self.lbl_ex_tl_font_size = ttk.Label(self.lf_ex_tl, text="Font Size")
        self.lbl_ex_tl_font_size.pack(side="left", padx=5, pady=5)

        self.spn_ex_tl_font_size = ttk.Spinbox(
            self.lf_ex_tl,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(self.number_only), "%P"),
            command=lambda: sj.save_key("tb_ex_tl_font_size", int(self.spn_ex_tl_font_size.get()))
            or self.preview_changes_tb(),
            width=10,
        )
        self.spn_ex_tl_font_size.bind(
            "<KeyRelease>",
            lambda e: self.verifyMaxNumber(
                self.spn_ex_tl_font_size,
                3,
                120,
                lambda: sj.save_key("tb_ex_tl_font_size", int(self.spn_ex_tl_font_size.get())) or self.preview_changes_tb(),
            ),
        )
        self.spn_ex_tl_font_size.pack(side="left", padx=5, pady=5)

        self.cbtn_ex_tl_font_bold = ttk.Checkbutton(
            self.lf_ex_tl,
            text="Bold",
            command=lambda: sj.save_key("tb_ex_tl_font_bold", self.cbtn_ex_tl_font_bold.instate(["selected"]))
            or self.preview_changes_tb(),
        )
        self.cbtn_ex_tl_font_bold.pack(side="left", padx=5, pady=5)

        self.lbl_ex_tl_font_color = ttk.Label(self.lf_ex_tl, text="Font Color")
        self.lbl_ex_tl_font_color.pack(side="left", padx=5, pady=5)

        self.entry_ex_tl_font_color = ttk.Entry(self.lf_ex_tl, width=10)
        self.entry_ex_tl_font_color.pack(side="left", padx=5, pady=5)
        self.entry_ex_tl_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_font_color, self.entry_ex_tl_font_color.get(), self.root)
            or sj.save_key("tb_ex_tl_font_color", self.entry_ex_tl_font_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tl_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tl_bg_color = ttk.Label(self.lf_ex_tl, text="Background Color")
        self.lbl_ex_tl_bg_color.pack(side="left", padx=5, pady=5)

        self.entry_ex_tl_bg_color = ttk.Entry(self.lf_ex_tl, width=10)
        self.entry_ex_tl_bg_color.pack(side="left", padx=5, pady=5)
        self.entry_ex_tl_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_bg_color, self.entry_ex_tl_bg_color.get(), self.root)
            or sj.save_key("tb_ex_tl_bg_color", self.entry_ex_tl_bg_color.get())
            or self.preview_changes_tb(),
        )
        self.entry_ex_tl_bg_color.bind("<Key>", lambda e: "break")

        # PREVIEW
        self.f_textbox_2 = ttk.Frame(self.ft_textbox)
        self.f_textbox_2.pack(side="top", fill="x", pady=5)

        self.f_textbox_3 = ttk.Frame(self.ft_textbox)
        self.f_textbox_3.pack(side="top", fill="x", pady=5)

        self.tb_preview_1 = tk.Text(
            self.f_textbox_2,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(
                sj.cache["tb_mw_tc_font"],
                sj.cache["tb_mw_tc_font_size"],
                "bold" if sj.cache["tb_mw_tc_font_bold"] else "normal",
            ),
        )
        self.tb_preview_1.bind("<Key>", "break")
        self.tb_preview_1.insert("end", "TC Main window:\n" + PREVIEW_WORDS)
        self.tb_preview_1.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        self.tb_preview_2 = tk.Text(
            self.f_textbox_2,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(
                sj.cache["tb_mw_tl_font"],
                sj.cache["tb_mw_tl_font_size"],
                "bold" if sj.cache["tb_mw_tl_font_bold"] else "normal",
            ),
        )
        self.tb_preview_2.bind("<Key>", "break")
        self.tb_preview_2.insert("end", "TL Main window:\n" + PREVIEW_WORDS)
        self.tb_preview_2.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        self.tb_preview_3 = tk.Text(
            self.f_textbox_3,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(
                sj.cache["tb_ex_tc_font"],
                sj.cache["tb_ex_tc_font_size"],
                "bold" if sj.cache["tb_ex_tc_font_bold"] else "normal",
            ),
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
            font=(
                sj.cache["tb_ex_tl_font"],
                sj.cache["tb_ex_tl_font_size"],
                "bold" if sj.cache["tb_ex_tl_font_bold"] else "normal",
            ),
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
        threading.Thread(target=self.f_general.delete_log_on_start, daemon=True).start()
        threading.Thread(target=self.f_general.delete_temp_on_start, daemon=True).start()

    def save_win_size(self):
        """
        Save window size
        """
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w > 600 and h > 300:
            sj.save_key("sw_size", f"{w}x{h}")

    def on_close(self):
        self.save_win_size()
        self.root.withdraw()

    def show(self):
        self.root.after(0, self.root.deiconify)

        if not self.f_general.model_checked:
            threading.Thread(target=self.f_general.check_model_on_first_open, daemon=True).start()

    def bind_focus_on_frame_recursively(self, root_widget):
        widgets = root_widget.winfo_children()

        # now check if there are any children of the children
        for widget in widgets:
            if len(widget.winfo_children()) > 0:
                self.bind_focus_on_frame_recursively(widget)

            if isinstance(widget, tk.Frame) or isinstance(widget, ttk.Frame) or isinstance(widget, tk.LabelFrame):
                widget.bind("<Button-1>", lambda event: self.root.focus_set())  # type: ignore

    def init_setting_once(self):
        # tc
        self.spn_tc_rate.set(sj.cache["transcribe_rate"])

        # whisper settings
        cbtn_invoker(sj.cache["condition_on_previous_text"], self.cbtn_condition_on_previous_text)
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
        cbtn_invoker(sj.cache["libre_https"], self.cbtn_libre_https)

        # tb
        self.init_tb_settings(sj.cache)
        cbtn_invoker(sj.cache["tb_mw_tc_font_bold"], self.cbtn_mw_tc_font_bold)
        cbtn_invoker(sj.cache["tb_mw_tl_font_bold"], self.cbtn_mw_tl_font_bold)
        cbtn_invoker(sj.cache["tb_ex_tc_font_bold"], self.cbtn_ex_tc_font_bold)
        cbtn_invoker(sj.cache["tb_ex_tl_font_bold"], self.cbtn_ex_tl_font_bold)

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

        gc.mw.tb_transcribed.configure(
            font=(
                self.cb_mw_tc_font.get(),
                int(self.spn_mw_tc_font_size.get()),
                "bold" if self.cbtn_mw_tc_font_bold.instate(["selected"]) else "normal",
            )
        )
        self.tb_preview_1.configure(
            font=(
                self.cb_mw_tc_font.get(),
                int(self.spn_mw_tc_font_size.get()),
                "bold" if self.cbtn_mw_tc_font_bold.instate(["selected"]) else "normal",
            )
        )

        gc.mw.tb_translated.configure(
            font=(
                self.cb_mw_tl_font.get(),
                int(self.spn_mw_tl_font_size.get()),
                "bold" if self.cbtn_mw_tl_font_bold.instate(["selected"]) else "normal",
            )
        )
        self.tb_preview_2.configure(
            font=(
                self.cb_mw_tl_font.get(),
                int(self.spn_mw_tl_font_size.get()),
                "bold" if self.cbtn_mw_tl_font_bold.instate(["selected"]) else "normal",
            )
        )

        assert gc.ex_tcw is not None
        gc.ex_tcw.lbl_text.configure(
            font=(
                self.cb_ex_tc_font.get(),
                int(self.spn_ex_tc_font_size.get()),
                "bold" if self.cbtn_ex_tc_font_bold.instate(["selected"]) else "normal",
            ),
            foreground=self.entry_ex_tc_font_color.get(),
            background=self.entry_ex_tc_bg_color.get(),
        )
        self.tb_preview_3.configure(
            font=(
                self.cb_ex_tc_font.get(),
                int(self.spn_ex_tc_font_size.get()),
                "bold" if self.cbtn_ex_tc_font_bold.instate(["selected"]) else "normal",
            ),
            foreground=self.entry_ex_tc_font_color.get(),
            background=self.entry_ex_tc_bg_color.get(),
        )

        assert gc.ex_tlw is not None
        gc.ex_tlw.lbl_text.configure(
            font=(
                self.cb_ex_tl_font.get(),
                int(self.spn_ex_tl_font_size.get()),
                "bold" if self.cbtn_ex_tl_font_bold.instate(["selected"]) else "normal",
            ),
            foreground=self.entry_ex_tl_font_color.get(),
            background=self.entry_ex_tl_bg_color.get(),
        )
        self.tb_preview_4.configure(
            font=(
                self.cb_ex_tl_font.get(),
                int(self.spn_ex_tl_font_size.get()),
                "bold" if self.cbtn_ex_tl_font_bold.instate(["selected"]) else "normal",
            ),
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
