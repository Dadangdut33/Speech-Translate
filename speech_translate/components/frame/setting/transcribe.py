from os import listdir, path, remove
from tkinter import filedialog, ttk, Frame, LabelFrame, Toplevel, StringVar, Event, Menu
from typing import Literal, Union
from speech_translate.components.custom.checkbutton import CustomCheckButton
from speech_translate.components.custom.message import MBoxText, mbox
from datetime import datetime

from stable_whisper import result_to_ass, result_to_srt_vtt, result_to_tsv

from speech_translate.globals import sj, gc
from speech_translate._path import dir_export
from speech_translate.utils.helper import filename_only, popup_menu, start_file, up_first_case
from speech_translate.utils.whisper.helper import get_temperature, parse_args_stable_ts
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

        self.f_whisper_args_0 = ttk.Frame(self.lf_whisper_args)
        self.f_whisper_args_0.pack(side="top", fill="x", pady=(10, 5), padx=5)

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

        self.cbtn_use_faster_whisper = CustomCheckButton(
            self.f_whisper_args_0,
            sj.cache["use_faster_whisper"],
            lambda x: sj.save_key("use_faster_whisper", x),
            text="Use Faster Whisper",
            style="Switch.TCheckbutton",
        )
        self.cbtn_use_faster_whisper.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_use_faster_whisper,
            "Use faster whisper.\n\nDefault is checked",
        )

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
            command=lambda: self.change_decoding_preset(self.radio_decoding_var.get()),
        )
        self.radio_decoding_1.pack(side="left", padx=5)
        self.radio_decoding_2 = ttk.Radiobutton(
            self.f_decoding_1,
            text="Beam Search (Accurate)",
            variable=self.radio_decoding_var,
            value="beam search",
            command=lambda: self.change_decoding_preset(self.radio_decoding_var.get()),
        )
        self.radio_decoding_2.pack(side="left", padx=5)
        self.radio_decoding_3 = ttk.Radiobutton(
            self.f_decoding_1,
            text="Custom",
            variable=self.radio_decoding_var,
            value="custom",
            command=lambda: self.change_decoding_preset(self.radio_decoding_var.get()),
        )
        self.radio_decoding_3.pack(side="left", padx=5)

        # 2
        self.lbl_temperature = ttk.Label(self.f_decoding_2, text="Temperature", width=17)
        self.lbl_temperature.pack(side="left", padx=5)
        self.entry_temperature = ttk.Entry(self.f_decoding_2)
        self.entry_temperature.insert(0, sj.cache["temperature"])
        self.entry_temperature.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_temperature.bind("<FocusOut>", lambda e: self.verify_temperature(self.entry_temperature.get()))
        self.entry_temperature.bind("<Return>", lambda e: self.verify_temperature(self.entry_temperature.get()))
        tk_tooltips(
            [self.lbl_temperature, self.entry_temperature],
            "Temperature for sampling. It can be a tuple of temperatures, which will be successively used upon failures "
            "according to either `compression_ratio_threshold` or `logprob_threshold`."
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
        self.entry_whisper_args.bind("<Return>", lambda e: self.verify_raw_args(self.entry_whisper_args.get()))
        tk_tooltip(self.entry_whisper_args, "Whisper extra arguments.\n\nDefault is empty")

        hint = (
            "Command line arguments to be used. (Usage value shown as example here are only for reference)"
            #
            "\n\n# [vad]\n* description: Whether to run Voice Activity Detection (VAD) to remove non-speech segment before applying Whisper model (removes hallucinations)"
            "\n* type: bool, default False \n* usage: --vad True"
            "\n\n# [detect_disfluencies]\n* description: Whether to try to detect disfluencies, marking them as special words [*]"
            "\n* type: bool, default False \n* usage: --detect_disfluencies True"
            "\n\n# [recompute_all_timestamps]\n* description: Do not rely at all on Whisper timestamps (Experimental option: did not bring any improvement, but could be useful in cases where Whipser segment timestamp are wrong by more than 0.5 seconds)"
            "\n* type: bool, default False \n* usage: --recompute_all_timestamps True"
            "\n\n# [punctuations_with_words]\n*Whether to include punctuations in the words"
            "\n* type: bool, default True \n* usage: --detect_disfluencies False"
            "\n\n# [patience]\n* description: Optional patience value to use in beam decoding, as in https://arxiv.org/abs/2204.05424, 1.0 is equivalent to conventional beam search"
            "\n* type: float, default None \n* usage: --patience 1.0"
            "\n\n# [length_penalty]\n* description: optional token length penalty coefficient (alpha) as in https://arxiv.org/abs/1609.08144, uses simple length normalization by default"
            "\n* type: float, default None \n* usage: --length_penalty 0.0"
            "\n\n# [fp16]\n* description: Whether to perform inference in fp16; Automatic by default (True if GPU available, False otherwise)"
            "\n* type: bool, default None \n* usage: --fp16 true"
            "\n\n# [threads]\n* description: Number of threads used by torch for CPU inference; supercedes MKL_NUM_THREADS/OMP_NUM_THREADS"
            "\n* type: int, default 0 \n* usage: --threads 2"
            "\n\n# [compute_confidence]\n*description: Whether to compute confidence scores for words"
            "\n* type: bool, default True \n* usage: --compute_confidence False"
            "\n\n# [verbose]\n*description: Whether to print out the progress and debug messages of Whisper"
            "\n* type: bool, default False \n* usage: --verbose True"
            "\n\n# [plot]\n* description: Show plot of word alignments (result will be saved automatically in output folder)"
            "\n* type: bool, default False \n* usage: --plot"
            "\n\n# [debug]\n* description: Print some debug information about word alignment"
            "\n* type: bool, default False \n* usage: --debug"
            "\n\n# [naive]\n* description: Use naive approach, doing inference twice (once to get the transcription, once to get word timestamps and confidence scores)"
            "\n* type: bool, default False \n* usage: --naive"
        )
        CreateToolTipOnText(
            self.entry_whisper_args,
            hint,
            geometry="800x250",
            opacity=1.0,
            focus_out_bind=lambda: self.verify_raw_args(self.entry_whisper_args.get())
        )

        self.btn_help = ttk.Button(
            self.f_whisper_args_2,
            text="❔",
            command=lambda: MBoxText("whisper-params", self.root, "Whisper Args", hint, "700x300"),
            width=5,
        )
        self.btn_help.pack(side="left", padx=5)
        tk_tooltip(self.btn_help, "Click to see the available arguments.")

        # --------------------
        # export
        self.lf_export = LabelFrame(self.master, text="• Export")
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

        self.f_export_6 = ttk.Frame(self.lf_export)
        self.f_export_6.pack(side="top", fill="x", padx=5, pady=5)

        self.lbl_output_mode = ttk.Label(self.f_export_1, text="Mode", width=17)
        self.lbl_output_mode.pack(side="left", padx=5)

        def keep_one_enabled(value: bool, other_widget: ttk.Checkbutton):
            if not value:
                other_widget.configure(state="disabled")
            else:
                other_widget.configure(state="normal")

        self.cbtn_segment_level = CustomCheckButton(
            self.f_export_1,
            sj.cache["segment_level"],
            lambda x: sj.save_key("segment_level", x) or keep_one_enabled(x, self.cbtn_word_level),
            text="Segment Level",
            style="Switch.TCheckbutton",
        )
        self.cbtn_segment_level.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_segment_level,
            "Export the text in segment level.\n\n*Either segment level or word level must be enabled.\n\nDefault is checked",
            wrapLength=350
        )

        self.cbtn_word_level = CustomCheckButton(
            self.f_export_1,
            sj.cache["word_level"],
            lambda x: sj.save_key("word_level", x) or keep_one_enabled(x, self.cbtn_segment_level),
            text="Word Level",
            style="Switch.TCheckbutton",
        )
        self.cbtn_word_level.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_word_level,
            "Export the text in word level.\n\n*Either segment level or word level must be enabled.\n\nDefault is checked",
            wrapLength=350
        )

        self.lbl_export_to = ttk.Label(self.f_export_2, text="Export to", width=17)
        self.lbl_export_to.pack(side="left", padx=5)

        self.cbtn_export_txt = CustomCheckButton(
            self.f_export_2, "txt" in sj.cache["export_to"], lambda x: self.callback_export_to("txt", x), text="Text"
        )
        self.cbtn_export_txt.pack(side="left", padx=5)

        self.cbtn_export_json = CustomCheckButton(
            self.f_export_2, "json" in sj.cache["export_to"], lambda x: self.callback_export_to("json", x), text="JSON"
        )
        self.cbtn_export_json.pack(side="left", padx=5)

        self.cbtn_export_srt = CustomCheckButton(
            self.f_export_2, "srt" in sj.cache["export_to"], lambda x: self.callback_export_to("srt", x), text="SRT"
        )
        self.cbtn_export_srt.pack(side="left", padx=5)

        self.cbtn_export_ass = CustomCheckButton(
            self.f_export_2, "ass" in sj.cache["export_to"], lambda x: self.callback_export_to("ass", x), text="ASS"
        )
        self.cbtn_export_ass.pack(side="left", padx=5)

        self.cbtn_export_vtt = CustomCheckButton(
            self.f_export_2, "vtt" in sj.cache["export_to"], lambda x: self.callback_export_to("vtt", x), text="VTT"
        )
        self.cbtn_export_vtt.pack(side="left", padx=5)

        self.cbtn_export_tsv = CustomCheckButton(
            self.f_export_2, "tsv" in sj.cache["export_to"], lambda x: self.callback_export_to("tsv", x), text="TSV"
        )
        self.cbtn_export_tsv.pack(side="left", padx=5)

        self.cbtn_export_csv = CustomCheckButton(
            self.f_export_2, "csv" in sj.cache["export_to"], lambda x: self.callback_export_to("csv", x), text="CSV"
        )
        self.cbtn_export_csv.pack(side="left", padx=5)

        self.separator_fex_2 = ttk.Separator(self.f_export_2, orient="vertical")
        self.separator_fex_2.pack(side="left", padx=5, fill="y")

        self.cbtn_visaulize_suppression = CustomCheckButton(
            self.f_export_2,
            sj.cache["visualize_suppression"],
            lambda x: sj.save_key("visualize_suppression", x),
            text="Visualize Suppression",
            style="Switch.TCheckbutton",
        )
        self.cbtn_visaulize_suppression.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_visaulize_suppression,
            "visualize which parts of the audio will likely be suppressed (i.e. marked as silent).\n\nDefault is unchecked",
            wrapLength=350
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
        self.change_decoding_preset(sj.cache["decoding_preset"])
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
                self.entry_temperature.configure(state="normal")
                self.entry_temperature.delete(0, "end")
                self.entry_temperature.insert(0, "0.0")
                self.entry_temperature.configure(state="disabled")
                sj.save_key("temperature", "0.0")

                self.spn_best_of.set("")
                sj.save_key("best_of", None)

                self.spn_beam_size.set("")
                sj.save_key("beam_size", None)
            elif value == "beam search":
                self.entry_temperature.configure(state="normal")
                self.entry_temperature.delete(0, "end")
                self.entry_temperature.insert(0, "0.0, 0.2, 0.4, 0.6, 0.8, 1.0")
                self.entry_temperature.configure(state="disabled")
                sj.save_key("temperature", "0.0, 0.2, 0.4, 0.6, 0.8, 1.0")

                self.spn_best_of.set(5)
                sj.save_key("best_of", 5)

                self.spn_beam_size.set(5)
                sj.save_key("beam_size", 5)

    def callback_export_to(
        self, value: Union[Literal["txt"], Literal["csv"], Literal["json"], Literal["srt"], Literal["ass"], Literal["vtt"],
                           Literal["tsv"]], add: bool
    ):
        try:
            export_list = sj.cache["export_to"].copy()
            if add:
                export_list.append(value)
            else:
                export_list.remove(value)

            sj.save_key("export_to", export_list)
        except Exception:
            pass

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

    def verify_temperature(self, value: str):
        status, msg = get_temperature(value)
        if not status:
            self.entry_temperature.delete(0, "end")
            self.entry_temperature.insert(0, sj.cache["temperature"])
            mbox("Invalid Temperature Options", f"{msg}", 2, self.root)

            return

        sj.save_key("temperature", value)

    def verify_raw_args(self, value: str):
        if len(value) == 0:
            return

        loop_for = ["load", "transcribe", "align", "refine", "save"]
        check_for_save = [result_to_ass, result_to_srt_vtt, result_to_tsv]
        kwargs = {"show_parsed": False}

        for el in loop_for:
            if el != "save":
                res = parse_args_stable_ts(value, el, **kwargs)
                if not res["success"]:
                    mbox("Invalid Stable Whisper Arguments", f"{res['msg']}", 2, self.root)
                    return
            else:
                # save, special. Need to pass the save method
                for method in check_for_save:
                    res = parse_args_stable_ts(value, el, method, **kwargs)
                    if not res["success"]:
                        mbox("Invalid Stable Whisper Arguments", f"{res['msg']}", 2, self.root)
                        return

        sj.save_key("whisper_args", value)
