from tkinter import ttk, Frame, LabelFrame, Toplevel
from typing import Union
from speech_translate.components.custom.message import MBoxText, mbox

from speech_translate.globals import sj
from speech_translate.utils.helper import cbtn_invoker

from speech_translate.components.custom.tooltip import CreateToolTipOnText, tk_tooltip, tk_tooltips
from speech_translate.components.custom.spinbox import SpinboxNumOnly
from speech_translate.utils.whisper.helper import convert_str_options_to_dict, get_temperature


class SettingTranscribe:
    """
    Textboox tab in setting window.
    """
    def __init__(self, root: Toplevel, master_frame: Union[ttk.Frame, Frame]):
        self.root = root
        self.master = master_frame

        # ------------------ Options ------------------
        # whisper args
        self.lf_whisper_args = LabelFrame(self.master, text="Whisper Options")
        self.lf_whisper_args.pack(side="top", fill="x", pady=5, padx=5)

        self.f_whisper_args_1 = ttk.Frame(self.lf_whisper_args)
        self.f_whisper_args_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_whisper_args_2 = ttk.Frame(self.lf_whisper_args)
        self.f_whisper_args_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_whisper_args_3 = ttk.Frame(self.lf_whisper_args)
        self.f_whisper_args_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_whisper_args_4 = ttk.Frame(self.lf_whisper_args)
        self.f_whisper_args_4.pack(side="top", fill="x", pady=5, padx=5)

        self.f_whisper_args_5 = ttk.Frame(self.lf_whisper_args)
        self.f_whisper_args_5.pack(side="top", fill="x", pady=5, padx=5)

        self.cbtn_condition_on_previous_text = ttk.Checkbutton(
            self.f_whisper_args_1, text="Condition on previous text", style="Switch.TCheckbutton"
        )
        self.cbtn_condition_on_previous_text.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_condition_on_previous_text,
            "if True, the previous output of the model is provided as a prompt for the next window;"
            "\n\nDisabling may make the text inconsistent across windows, but the model becomes less prone to getting stuck "
            "in a failure loop, such as repetition looping or timestamps going out of sync."
            "\n\nDefault value is true/checked",
        )

        self.lbl_compression_ratio_threshold = ttk.Label(self.f_whisper_args_2, text="Compression threshold", width=21)
        self.lbl_compression_ratio_threshold.pack(side="left", padx=5)

        self.spn_compression_ratio_threshold = SpinboxNumOnly(
            self.root, self.f_whisper_args_2, -100, 100, lambda x: sj.save_key("compression_ratio_threshold", float(x)), True
        )
        self.spn_compression_ratio_threshold.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_compression_ratio_threshold, self.spn_compression_ratio_threshold],
            "Compression ratio threshold.\n\nIf the gzip compression ratio is above this value, treat as failed."
            "\n\nDefault value is 2.4",
        )

        self.lbl_logprob_threshold = ttk.Label(self.f_whisper_args_2, text="Logprob threshold", width=21)
        self.lbl_logprob_threshold.pack(side="left", padx=5)

        self.spn_logprob_threshold = SpinboxNumOnly(
            self.root, self.f_whisper_args_2, -100, 100, lambda x: sj.save_key("logprob_threshold", float(x)), True
        )
        self.spn_logprob_threshold.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_logprob_threshold, self.spn_logprob_threshold],
            "If the average log probability over sampled tokens is below this value, treat as failed."
            "\n\nDefault value is -1.0",
        )

        self.lbl_no_speech_threshold = ttk.Label(self.f_whisper_args_3, text="No speech threshold", width=21)
        self.lbl_no_speech_threshold.pack(side="left", padx=5)

        self.spn_no_speech_threshold = SpinboxNumOnly(
            self.root, self.f_whisper_args_3, -100, 100, lambda x: sj.save_key("no_speech_threshold", float(x)), True
        )
        self.spn_no_speech_threshold.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_no_speech_threshold, self.spn_no_speech_threshold],
            """If the no_speech probability is higher than this value AND the average log probability
        \rover sampled tokens is below `logprob_threshold`, consider the segment as silent.\n\nDefault value is 0.6""",
        )

        self.lbl_temperature = ttk.Label(self.f_whisper_args_3, text="Temperature", width=18)
        self.lbl_temperature.pack(side="left", padx=5)

        self.entry_temperature = ttk.Entry(self.f_whisper_args_3)
        self.entry_temperature.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_temperature.bind("<KeyRelease>", lambda e: sj.save_key("temperature", self.entry_temperature.get()))
        tk_tooltips(
            [self.lbl_temperature, self.entry_temperature],
            "Temperature for sampling. It can be a tuple of temperatures, which will be successively used upon failures "
            "according to either `compression_ratio_threshold` or `logprob_threshold`."
            "\n\nDefault is 0.0, 0.2, 0.4, 0.6, 0.8, 1.0",
        )

        self.btn_verify_temperature = ttk.Button(self.f_whisper_args_3, text="Verify", command=lambda: self.verifyTemp())
        self.btn_verify_temperature.pack(side="left", padx=5)
        tk_tooltip(self.btn_verify_temperature, "Verify temperature input.")

        self.lbl_initial_prompt = ttk.Label(self.f_whisper_args_4, text="Initial prompt", width=21)
        self.lbl_initial_prompt.pack(side="left", padx=5)

        self.entry_initial_prompt = ttk.Entry(self.f_whisper_args_4)
        self.entry_initial_prompt.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_initial_prompt.bind(
            "<KeyRelease>", lambda e: sj.save_key("initial_prompt", self.entry_initial_prompt.get())
        )
        tk_tooltips(
            [self.lbl_initial_prompt, self.entry_initial_prompt],
            "optional text to provide as a prompt for the first window.\n\nDefault is empty",
        )

        self.lbl_whisper_args = ttk.Label(self.f_whisper_args_5, text="Extra parameter", width=21)
        self.lbl_whisper_args.pack(side="left", padx=5)

        self.entry_whisper_extra_args = ttk.Entry(self.f_whisper_args_5)
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
            '\nprompt: str or [int]\n--prompt "hello world" or --prompt [1, 2, 3]'
            #
            "\n\n# Text or tokens to prefix the current context"
            '\nprefix: str or [int]\n--prefix "hello world" or --prefix [1, 2, 3]'
            #
            "\n\n# Text or tokens for the previous context"
            "\nsuppress_blank: bool\n--suppress_blank true"
            #
            '\n\n# List of tokens ids (or comma-separated token ids) to suppress\n# "-1" will suppress a set of symbols as '
            "defined in `tokenizer.non_speech_tokens()`"
            '\nsuppress_tokens: str or [int]\n--suppress_tokens "-1" or --suppress_tokens [-1, 0]'
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
            self.f_whisper_args_5,
            text="❔",
            command=lambda: MBoxText("whisper-params", self.root, "Whisper Args", hint),
            width=5,
        )
        self.btn_help.pack(side="left", padx=5)
        tk_tooltip(self.btn_help, "Click to see the available arguments.")

        self.btn_verify = ttk.Button(self.f_whisper_args_5, text="Verify", command=lambda: self.verifyWhisperArgs())
        self.btn_verify.pack(side="left", padx=5)
        tk_tooltip(self.btn_verify, "Verify the extra arguments.")

        # --------------------------
        self.init_setting_once()

    # ------------------ Functions ------------------
    def init_setting_once(self):
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

        self.configure_commands()

    def configure_commands(self):
        """
        To prevent the command from being called multiple times, we need to configure
        the command just once after the setting is initialized
        """
        self.spn_compression_ratio_threshold.configure(
            command=lambda: sj.save_key("compression_ratio_threshold", float(self.spn_compression_ratio_threshold.get()))
        )
        self.spn_logprob_threshold.configure(
            command=lambda: sj.save_key("logprob_threshold", float(self.spn_logprob_threshold.get()))
        )
        self.spn_no_speech_threshold.configure(
            command=lambda: sj.save_key("no_speech_threshold", float(self.spn_no_speech_threshold.get()))
        )
        self.cbtn_condition_on_previous_text.configure(
            command=lambda: sj.
            save_key("condition_on_previous_text", self.cbtn_condition_on_previous_text.instate(["selected"]))
        )

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
