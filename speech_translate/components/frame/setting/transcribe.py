from os import listdir, path, remove
from tkinter import filedialog, ttk, Frame, LabelFrame, Toplevel, StringVar, Event, Menu
from typing import Union
from speech_translate.components.custom.checkbutton import CustomCheckButton
from speech_translate.components.custom.message import MBoxText, mbox
from datetime import datetime

from speech_translate.globals import sj, gc
from speech_translate._path import dir_export
from speech_translate.utils.helper import filename_only, popup_menu, start_file, up_first_case
from speech_translate.utils.whisper.helper import convert_str_options_to_dict, get_temperature
from speech_translate.components.custom.tooltip import CreateToolTipOnText, tk_tooltip, tk_tooltips
from speech_translate.components.custom.spinbox import SpinboxNumOnly


class SettingTranscribe:
    """
    Textboox tab in setting window.
    """
    def __init__(self, root: Toplevel, master_frame: Union[ttk.Frame, Frame]):
        self.root = root
        self.master = master_frame

        # ------------------ Options ------------------
        # whisper args
        self.lf_whisper_args = LabelFrame(self.master, text="• Whisper Options")
        self.lf_whisper_args.pack(side="top", fill="x", pady=5, padx=5)

        self.lf_decoding_options = ttk.LabelFrame(self.lf_whisper_args, text="Decoding")
        self.lf_decoding_options.pack(side="top", fill="x", pady=5, padx=5)

        self.f_decoding_1 = ttk.Frame(self.lf_decoding_options)
        self.f_decoding_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_decoding_2 = ttk.Frame(self.lf_decoding_options)
        self.f_decoding_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_decoding_3 = ttk.Frame(self.lf_decoding_options)
        self.f_decoding_3.pack(side="top", fill="x", pady=(5, 10), padx=5)

        self.lf_threshold_options = ttk.LabelFrame(self.lf_whisper_args, text="Threshold")
        self.lf_threshold_options.pack(side="top", fill="x", pady=5, padx=5)

        self.f_threshold_1 = ttk.Frame(self.lf_threshold_options)
        self.f_threshold_1.pack(side="top", fill="x", pady=(5, 10), padx=5)

        self.f_whisper_args_1 = ttk.Frame(self.lf_whisper_args)
        self.f_whisper_args_1.pack(side="top", fill="x", pady=(10, 5), padx=5)

        self.f_whisper_args_2 = ttk.Frame(self.lf_whisper_args)
        self.f_whisper_args_2.pack(side="top", fill="x", pady=(5, 10), padx=5)

        # decoding options
        self.radio_decoding_var = StringVar()
        # 1
        self.lbl_decoding_preset = ttk.Label(self.f_decoding_1, text="Decoding Preset", width=17)
        self.lbl_decoding_preset.pack(side="left", padx=5)
        self.radio_decoding_1 = ttk.Radiobutton(
            self.f_decoding_1,
            text="Greedy (Efficient)",
            variable=self.radio_decoding_var,
            value="greedy",
            command=lambda: sj.save_key("decoding_preset", self.radio_decoding_var.get()),
        )
        self.radio_decoding_1.pack(side="left", padx=5)
        self.radio_decoding_2 = ttk.Radiobutton(
            self.f_decoding_1,
            text="Beam Search (Accurate)",
            variable=self.radio_decoding_var,
            value="beam search",
            command=lambda: sj.save_key("decoding_preset", self.radio_decoding_var.get()),
        )
        self.radio_decoding_2.pack(side="left", padx=5)
        self.radio_decoding_3 = ttk.Radiobutton(
            self.f_decoding_1,
            text="Custom",
            variable=self.radio_decoding_var,
            value="custom",
            command=lambda: sj.save_key("decoding_preset", self.radio_decoding_var.get()),
        )
        self.radio_decoding_3.pack(side="left", padx=5)

        # 2
        self.lbl_temperature = ttk.Label(self.f_decoding_2, text="Temperature", width=17)
        self.lbl_temperature.pack(side="left", padx=5)
        self.entry_temperature = ttk.Entry(self.f_decoding_2)
        self.entry_temperature.insert(0, sj.cache["temperature"])
        self.entry_temperature.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_temperature.bind("<KeyRelease>", lambda e: sj.save_key("temperature", self.entry_temperature.get()))
        tk_tooltips(
            [self.lbl_temperature, self.entry_temperature],
            "Temperature for sampling. It can be a tuple of temperatures, which will be successively used upon failures "
            "according to either `compression_ratio_threshold` or `logprob_threshold`."
            "\n\nDefault is 0.0",
        )

        # 3
        self.lbl_best_of = ttk.Label(self.f_decoding_3, text="Best of", width=17)
        self.lbl_best_of.pack(side="left", padx=5)
        self.spn_best_of = SpinboxNumOnly(
            self.root,
            self.f_decoding_3,
            -100,
            100,
            lambda x: sj.save_key("best_of",
                                  int(x) if x != "" else None),
            initial_value=sj.cache["best_of"],
            allow_empty=True,
            num_float=True,
            width=25,
        )
        self.spn_best_of.pack(side="left", padx=5)
        tk_tooltips([self.lbl_best_of, self.spn_best_of], "Number of candidates when sampling with non-zero temperature")

        self.lbl_beam_size = ttk.Label(self.f_decoding_3, text="Beam size", width=17)
        self.lbl_beam_size.pack(side="left", padx=5)
        self.spn_beam_size = SpinboxNumOnly(
            self.root,
            self.f_decoding_3,
            -100,
            100,
            lambda x: sj.save_key("beam_size",
                                  int(x) if x != "" else None),
            initial_value=sj.cache["beam_size"],
            allow_empty=True,
            num_float=True,
            width=25,
        )
        self.spn_beam_size.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_beam_size, self.spn_beam_size],
            "Number of beams in beam search, only applicable when temperature is zero"
        )

        # threshold
        self.lbl_compression_ratio_threshold = ttk.Label(self.f_threshold_1, text="Compression Ratio", width=17)
        self.lbl_compression_ratio_threshold.pack(side="left", padx=5)
        self.spn_compression_ratio_threshold = SpinboxNumOnly(
            self.root,
            self.f_threshold_1,
            -10,
            10,
            lambda x: sj.save_key("compression_ratio_threshold", float(x)),
            initial_value=sj.cache["compression_ratio_threshold"],
            num_float=True,
            width=25,
        )
        self.spn_compression_ratio_threshold.pack(side="left", padx=5)

        self.lbl_logprob_threshold = ttk.Label(self.f_threshold_1, text="Logprob", width=17)
        self.lbl_logprob_threshold.pack(side="left", padx=5)
        self.spn_logprob_threshold = SpinboxNumOnly(
            self.root,
            self.f_threshold_1,
            -10,
            10,
            lambda x: sj.save_key("logprob_threshold", float(x)),
            initial_value=sj.cache["logprob_threshold"],
            num_float=True,
            width=25,
        )
        self.spn_logprob_threshold.pack(side="left", padx=5)

        self.no_speech_threshold = ttk.Label(self.f_threshold_1, text="No Speech", width=17)
        self.no_speech_threshold.pack(side="left", padx=5)
        self.spn_no_speech_threshold = SpinboxNumOnly(
            self.root,
            self.f_threshold_1,
            -10,
            10,
            lambda x: sj.save_key("no_speech_threshold", float(x)),
            initial_value=sj.cache["no_speech_threshold"],
            num_float=True,
            width=25,
        )
        self.spn_no_speech_threshold.pack(side="left", padx=5)

        # other whisper args
        self.lbl_initial_prompt = ttk.Label(self.f_whisper_args_1, text="Initial Prompt", width=17)
        self.lbl_initial_prompt.pack(side="left", padx=5)
        self.entry_initial_prompt = ttk.Entry(self.f_whisper_args_1, width=30)
        self.entry_initial_prompt.insert(0, sj.cache["initial_prompt"])
        self.entry_initial_prompt.pack(side="left", padx=5, fill="x")
        self.entry_initial_prompt.bind(
            "<KeyRelease>", lambda e: sj.save_key("initial_prompt", self.entry_initial_prompt.get())
        )
        tk_tooltips(
            [self.lbl_initial_prompt, self.entry_initial_prompt],
            "optional text to provide as a prompt for the first window.\n\nDefault is empty",
        )

        self.lbl_suppress_tokens = ttk.Label(self.f_whisper_args_1, text="Supress Token", width=17)
        self.lbl_suppress_tokens.pack(side="left", padx=5)
        self.entry_supress_tokens = ttk.Entry(self.f_whisper_args_1, width=30)
        self.entry_supress_tokens.pack(side="left", padx=5, fill="x")
        self.entry_supress_tokens.bind(
            "<KeyRelease>", lambda e: sj.save_key("suppress_tokens", self.entry_supress_tokens.get())
        )
        tk_tooltips(
            [self.lbl_suppress_tokens, self.entry_supress_tokens],
            "comma-separated list of token ids to suppress during sampling;"
            " '-1' will suppress most special characters except common punctuations.\n\nDefault is -1",
        )

        self.cbtn_condition_on_previous_text = CustomCheckButton(
            self.f_whisper_args_1,
            sj.cache["condition_on_previous_text"],
            lambda x: sj.save_key("condition_on_previous_text", x),
            text="Condition on previous text",
            style="Switch.TCheckbutton",
        )
        self.cbtn_condition_on_previous_text.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_condition_on_previous_text,
            "if True, the previous output of the model is provided as a prompt for the next window;"
            "\n\nDisabling may make the text inconsistent across windows, but the model becomes less prone to getting stuck "
            "in a failure loop, such as repetition looping or timestamps going out of sync."
            "\n\nDefault value is true/checked",
        )

        # 3
        self.lbl_whisper_args = ttk.Label(self.f_whisper_args_2, text="Raw Arguments", width=17)
        self.lbl_whisper_args.pack(side="left", padx=5)
        self.entry_whisper_args = ttk.Entry(self.f_whisper_args_2)
        self.entry_whisper_args.insert(0, sj.cache["whisper_args"])
        self.entry_whisper_args.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_whisper_args.bind("<KeyRelease>", lambda e: sj.save_key("whisper_args", self.entry_whisper_args.get()))
        tk_tooltip(self.entry_whisper_args, "Whisper extra arguments.\n\nDefault is empty")

        hint = (
            "Command line arguments to be used."
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
        CreateToolTipOnText(self.entry_whisper_args, hint, geometry="700x250")

        self.btn_help = ttk.Button(
            self.f_whisper_args_2,
            text="❔",
            command=lambda: MBoxText("whisper-params", self.root, "Whisper Args", hint),
            width=5,
        )
        self.btn_help.pack(side="left", padx=5)
        tk_tooltip(self.btn_help, "Click to see the available arguments.")

        self.btn_verify = ttk.Button(self.f_whisper_args_2, text="Verify", command=lambda: self.verifyWhisperArgs())
        self.btn_verify.pack(side="left", padx=5)
        tk_tooltip(self.btn_verify, "Verify the arguments.")

        # --------------------
        # export
        self.lf_export = LabelFrame(self.master, text="• Export")
        self.lf_export.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_1 = ttk.Frame(self.lf_export)
        self.f_export_1.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_2 = ttk.Frame(self.lf_export)
        self.f_export_2.pack(side="top", fill="x", padx=5, pady=(1, 5))

        self.f_export_3 = ttk.Frame(self.lf_export)
        self.f_export_3.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_4 = ttk.Frame(self.lf_export)
        self.f_export_4.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_5 = ttk.Frame(self.lf_export)
        self.f_export_5.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_6 = ttk.Frame(self.lf_export)
        self.f_export_6.pack(side="top", fill="x", padx=5, pady=5)

        self.lbl_export_to = ttk.Label(self.f_export_1, text="Export to", width=17)
        self.lbl_export_to.pack(side="left", padx=5)

        self.inv_padder = ttk.Label(self.f_export_2, width=17)
        self.inv_padder.pack(side="left", padx=5)

        # self.inv_padder_2 = ttk.Label(self.f_export_2, width=7)
        # self.inv_padder_2.pack(side="left", padx=(5, 7))

        def toggle_export_cbtn(enabled: bool, target_el: CustomCheckButton):
            if enabled:
                target_el.config(state="normal")
            else:
                target_el.config(state="disabled")

        self.cbtn_export_txt = CustomCheckButton(
            self.f_export_1,
            "txt" in sj.cache["export_to"],
            lambda x: self.callback_export_to("txt", x),
            text="Text",
            width=5
        )
        self.cbtn_export_txt.pack(side="left", padx=5)

        self.cbtn_export_json = CustomCheckButton(
            self.f_export_2,
            "json" in sj.cache["export_to"],
            lambda x: self.callback_export_to("json", x),
            text="JSON",
            width=5
        )
        self.cbtn_export_json.pack(side="left", padx=5)

        self.cbtn_export_srt = CustomCheckButton(
            self.f_export_1,
            "srt" in sj.cache["export_to"],
            lambda x: self.callback_export_to("srt", x) or toggle_export_cbtn(x, self.cbtn_export_srt_word),
            text="SRT",
            width=8
        )
        self.cbtn_export_srt.pack(side="left", padx=5)

        self.cbtn_export_srt_word = CustomCheckButton(
            self.f_export_2,
            "srt.words" in sj.cache["export_to"],
            lambda x: self.callback_export_to("srt.words", x),
            text="Per words",
            state="disabled" if "srt" not in sj.cache["export_to"] else "normal",
            width=8
        )
        self.cbtn_export_srt_word.pack(side="left", padx=5)

        self.cbtn_export_vtt = CustomCheckButton(
            self.f_export_1,
            "vtt" in sj.cache["export_to"],
            lambda x: self.callback_export_to("vtt", x) or toggle_export_cbtn(x, self.cbtn_export_vtt_word),
            text="VTT",
            width=8
        )
        self.cbtn_export_vtt.pack(side="left", padx=5)

        self.cbtn_export_vtt_word = CustomCheckButton(
            self.f_export_2,
            "vtt.words" in sj.cache["export_to"],
            lambda x: self.callback_export_to("vtt.words", x),
            text="Per words",
            state="disabled" if "vtt" not in sj.cache["export_to"] else "normal",
            width=8
        )
        self.cbtn_export_vtt_word.pack(side="left", padx=5)

        self.cbtn_export_tsv = CustomCheckButton(
            self.f_export_1,
            "tsv" in sj.cache["export_to"],
            lambda x: self.callback_export_to("tsv", x) or toggle_export_cbtn(x, self.cbtn_export_tsv_word),
            text="TSV",
            width=8
        )
        self.cbtn_export_tsv.pack(side="left", padx=5)

        self.cbtn_export_tsv_word = CustomCheckButton(
            self.f_export_2,
            "tsv.words" in sj.cache["export_to"],
            lambda x: self.callback_export_to("tsv.words", x),
            text="Per words",
            state="disabled" if "tsv" not in sj.cache["export_to"] else "normal",
            width=8
        )
        self.cbtn_export_tsv_word.pack(side="left", padx=5)

        self.cbtn_export_csv = CustomCheckButton(
            self.f_export_1,
            "csv" in sj.cache["export_to"],
            lambda x: self.callback_export_to("csv.words", x) or toggle_export_cbtn(x, self.cbtn_export_csv_word),
            text="CSV",
            width=8
        )
        self.cbtn_export_csv.pack(side="left", padx=5)

        self.cbtn_export_csv_word = CustomCheckButton(
            self.f_export_2,
            "csv.words" in sj.cache["export_to"],
            lambda x: self.callback_export_to("csv.words", x),
            text="Per Words",
            state="disabled" if "csv" not in sj.cache["export_to"] else "normal",
            width=8
        )
        self.cbtn_export_csv_word.pack(side="left", padx=5)

        tk_tooltips(
            [self.cbtn_export_srt_word, self.cbtn_export_vtt_word, self.cbtn_export_tsv_word, self.cbtn_export_csv_word],
            "Enable word level transcription, will export the text per words instead of per sentence to its own separated file."
        )

        self.lbl_export = ttk.Label(self.f_export_3, text="Export Folder", width=17)
        self.lbl_export.pack(side="left", padx=5)

        self.entry_export = ttk.Entry(self.f_export_3)
        self.entry_export.pack(side="left", padx=5, fill="x", expand=True)
        tk_tooltip(self.entry_export, "The folder where exported text from import file are saved.")

        self.btn_export_config = ttk.Button(
            self.f_export_3,
            image=gc.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_config_export)
        )
        self.btn_export_config.pack(side="left", padx=5)

        self.menu_config_export = Menu(self.master, tearoff=0)
        self.menu_config_export.add_command(
            label="Open", image=gc.open_emoji, compound="left", command=lambda: start_file(self.entry_export.get())
        )
        self.menu_config_export.add_separator()
        self.menu_config_export.add_command(
            label="Change Folder",
            image=gc.folder_emoji,
            compound="left",
            command=lambda: self.change_path("dir_export", self.entry_export)
        )
        self.menu_config_export.add_command(
            label="Set Back to Default",
            image=gc.reset_emoji,
            compound="left",
            command=lambda: self.path_default("dir_export", self.entry_export, dir_export),
        )
        self.menu_config_export.add_separator()
        self.menu_config_export.add_command(
            label="Empty Export Folder", image=gc.trash_emoji, compound="left", command=lambda: self.clear_export()
        )

        self.cbtn_auto_open_export = CustomCheckButton(
            self.f_export_3,
            sj.cache["auto_open_dir_export"],
            lambda x: sj.save_key("auto_open_dir_export", x),
            text="Auto open",
            style="Switch.TCheckbutton",
        )
        self.cbtn_auto_open_export.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_open_export,
            "Auto open the export folder after file import and the transcribe/translate process is done.",
            wrapLength=300,
        )

        def keybind_num(event: Event, widget: ttk.Entry):
            vsym = event.keysym
            vw = widget.get()
            v = event.char
            try:
                # check number or not
                int(v)  # pressed key
            except ValueError:
                # check value
                if vw == "":  # if empty
                    return "break"
                elif vsym == "minus":  # if minus
                    if "-" in vw:
                        replaced = vw.replace("-", "")
                        widget.delete(0, "end")
                        widget.insert(0, replaced)
                        return "break"
                    else:
                        replaced = "-" + vw
                        widget.delete(0, "end")
                        widget.insert(0, replaced)
                        return "break"

                # check pressed key
                if v != "\x08" and v != "":  # other than backspace and empty is not allowed
                    return "break"

        self.lbl_slice_file_start = ttk.Label(self.f_export_4, text="Slice file start", width=17)
        self.lbl_slice_file_start.pack(side="left", padx=5)
        self.spn_slice_file_start = SpinboxNumOnly(
            self.root,
            self.f_export_4,
            -256,
            256,
            lambda x: self.update_preview_export_format() or sj.save_key("file_slice_start", x),
            initial_value=sj.cache["file_slice_start"],
            allow_empty=True,
            delay=10,
        )
        self.spn_slice_file_start.pack(side="left", padx=5)

        self.lbl_slice_file_end = ttk.Label(self.f_export_4, text="Slice file end")
        self.lbl_slice_file_end.pack(side="left", padx=5)
        self.spn_slice_file_end = SpinboxNumOnly(
            self.root,
            self.f_export_4,
            -256,
            256,
            lambda x: self.update_preview_export_format() or sj.save_key("file_slice_end", x),
            initial_value=sj.cache["file_slice_end"],
            allow_empty=True,
            delay=10,
        )
        self.spn_slice_file_end.pack(side="left", padx=5)

        self.lbl_export_format = ttk.Label(self.f_export_5, text="Export format", width=17)
        self.lbl_export_format.pack(side="left", padx=5)
        self.entry_export_format = ttk.Entry(self.f_export_5)
        self.entry_export_format.insert(0, sj.cache["export_format"])
        self.entry_export_format.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_export_format.bind(
            "<KeyRelease>",
            lambda e: sj.save_key("export_format", self.entry_export_format.get()) or self.update_preview_export_format(),
        )

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
            self.f_export_5,
            image=gc.question_emoji,
            command=lambda: MBoxText("export-format", self.root, "Export formats", available_params),
            width=3,
        )
        self.btn_help_export_format.pack(side="left", padx=5)

        self.lbl_preview_export_format = ttk.Label(self.f_export_6, text="", width=17)  # padding helper
        self.lbl_preview_export_format.pack(side="left", padx=5, pady=(0, 5))

        self.lbl_preview_export_format_result = ttk.Label(self.f_export_6, text="...", foreground="gray")
        self.lbl_preview_export_format_result.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.lbl_preview_export_format_result,
            "Preview of the export format with the current settings\n"
            "Filename: this is an example video or audio file.mp4",
            wrapLength=350,
        )

        # --------------------------
        self.init_setting_once()

    # ------------------ Functions ------------------
    def init_setting_once(self):
        self.update_preview_export_format()

        if sj.cache["dir_export"] == "auto":
            self.path_default("dir_export", self.entry_export, dir_export, save=False, prompt=False)
        else:
            self.entry_export.configure(state="normal")
            self.entry_export.insert(0, sj.cache["dir_export"])
            self.entry_export.configure(state="readonly")

    def update_preview_export_format(self):
        try:
            filename = filename_only("this is an example video or audio file.mp4")
            task = "transcribe"
            short_task = "tc"
            slice_start = int(self.spn_slice_file_start.get()) if self.spn_slice_file_start.get() != "" else None
            slice_end = int(self.spn_slice_file_end.get()) if self.spn_slice_file_end.get() != "" else None

            assert gc.mw is not None
            save_name = datetime.now().strftime(self.entry_export_format.get())
            save_name = save_name.replace("{file}", filename[slice_start:slice_end])
            save_name = save_name.replace("{lang-source}", gc.mw.cb_source_lang.get())
            save_name = save_name.replace("{lang-target}", gc.mw.cb_target_lang.get())
            save_name = save_name.replace("{model}", gc.mw.cb_model.get())
            save_name = save_name.replace("{engine}", gc.mw.cb_engine.get())
            save_name = save_name.replace("{task}", task)
            save_name = save_name.replace("{task-short}", short_task)

            self.lbl_preview_export_format_result.configure(text=save_name)
        except Exception:
            pass

    def change_decoding_preset(self, value: str):
        self.radio_decoding_var.set(value)
        sj.save_key("decoding_preset", value)
        if value == "custom":
            self.entry_temperature.configure(state="normal")
            self.spn_best_of.configure(state="normal")
            self.spn_beam_size.configure(state="normal")
        else:
            self.entry_temperature.configure(state="disabled")
            self.spn_best_of.configure(state="disabled")
            self.spn_beam_size.configure(state="disabled")

            if value == "greedy":
                self.entry_temperature.delete(0, "end")
                self.entry_temperature.insert(0, "0.0")
                sj.save_key("temperature", "0.0")

                self.spn_best_of.set("")
                sj.save_key("best_of", None)

                self.spn_beam_size.set("")
                sj.save_key("beam_size", None)
            elif value == "beam search":
                self.entry_temperature.delete(0, "end")
                self.entry_temperature.insert(0, "1.0")
                sj.save_key("temperature", "0.0, 0.2, 0.4, 0.6, 0.8, 1.0")

                self.spn_best_of.set(5)
                sj.save_key("best_of", 5)

                self.spn_beam_size.set(5)
                sj.save_key("beam_size", 5)

    def callback_export_to(self, value: str, add: bool):
        export_list = sj.cache["export_to"].copy()
        if add:
            export_list.append(value)
        else:
            export_list.remove(value)

        sj.save_key("export_to", export_list)

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
            files = listdir(sj.cache["dir_export"])
            for file in files:
                remove(path.join(sj.cache["dir_export"], file))

    def verifyWhisperArgs(self):
        # get the values
        success, data = convert_str_options_to_dict(self.entry_whisper_args.get())

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
