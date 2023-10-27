import platform
import subprocess
from os import listdir, path, remove, startfile
from tkinter import filedialog, ttk, Frame, LabelFrame, Toplevel, StringVar, Event, Menu
from typing import Literal, Union
from speech_translate.components.custom.checkbutton import CustomCheckButton
from speech_translate.components.custom.message import MBoxText, mbox
from datetime import datetime

from stable_whisper import result_to_ass, result_to_srt_vtt, result_to_tsv, load_model, load_faster_whisper

from speech_translate.globals import sj, gc
from speech_translate._path import dir_export, parameters_text
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

        hint = """Command line arguments to be used. (Usage value shown as example here are only for reference). 

For more information, see https://github.com/jianfch/stable-ts or https://github.com/Dadangdut33/Speech-Translate/wiki
# [command]
* description of command
* type: data type, default xxx
* usage: --command xxx

# [device]
* description: device to use for PyTorch inference (A Cuda compatible GPU and PyTorch with CUDA support are still required for GPU / CUDA)
* type: str, default cuda
* usage: --device cpu

# [cpu_preload]
* description: load model into CPU memory first then move model to specified device; this reduces GPU memory usage when loading model.
* type: bool, default True
* usage: --cpu_preload True

# [dynamic_quantization]
* description: whether to apply Dynamic Quantization to model to reduce memory usage (~half less) and increase inference speed at cost of slight decrease in accuracy; Only for CPU; NOTE: overhead might make inference slower for models smaller than 'large'
* type: bool, default False
* usage: --dynamic_quantization

# [prepend_punctuations]
* description: Punctuations to prepend to the next word
* type: str, default "'“¿([{-"
* usage: --prepend_punctuations "<punctuation>"

# [append_punctuations]
* description: Punctuations to append to the previous word
* type: str, default "\"'.。,，!！?？:：”)]}、"
* usage: --append_punctuations "<punctuation>"

# [gap_padding]
* description: padding to prepend to each segment for word timing alignment; used to reduce the probability of the model predicting timestamps earlier than the first utterance
* type: str, default " ..."
* usage: --gap_padding "padding"

# [word_timestamps]
* description: extract word-level timestamps using the cross-attention pattern and dynamic time warping, and include the timestamps for each word in each segment; disabling this will prevent segments from splitting/merging properly.
* type: bool, default True
* usage: --word_timestamps True

# [regroup]
* description: whether to regroup all words into segments with more natural boundaries; specify a string for customizing the regrouping algorithm; ignored if [word_timestamps]=False.
* type: str, default "True"
* usage: --regroup "regroup_option"

# [ts_num]
* description: number of extra inferences to perform to find the mean timestamps
* type: int, default 0
* usage: --ts_num <number>

# [ts_noise]
* description: percentage of noise to add to audio_features to perform inferences for [ts_num]
* type: float, default 0.1
* usage: --ts_noise 0.1

# [suppress_silence]
* description: whether to suppress timestamps where audio is silent at segment-level and word-level if [suppress_word_ts]=True
* type: bool, default True
* usage: --suppress_silence True

# [suppress_word_ts]
* description: whether to suppress timestamps where audio is silent at word-level; ignored if [suppress_silence]=False
* type: bool, default True
* usage: --suppress_word_ts True

# [suppress_ts_tokens]
* description: whether to use silence mask to suppress silent timestamp tokens during inference; increases word accuracy in some cases, but tends to reduce 'verbatimness' of the transcript; ignored if [suppress_silence]=False
* type: bool, default False
* usage: --suppress_ts_tokens True

# [q_levels]
* description: quantization levels for generating timestamp suppression mask; acts as a threshold to marking sound as silent; fewer levels will increase the threshold of volume at which to mark a sound as silent
* type: int, default 20
* usage: --q_levels <number>

# [k_size]
* description: Kernel size for average pooling waveform to generate suppression mask; recommend 5 or 3; higher sizes will reduce detection of silence
* type: int, default 5
* usage: --k_size 5

# [time_scale]
* description: factor for scaling audio duration for inference; greater than 1.0 'slows down' the audio; less than 1.0 'speeds up' the audio; 1.0 is no scaling
* type: float
* usage: --time_scale <value>

# [vad]
* description: whether to use Silero VAD to generate timestamp suppression mask; Silero VAD requires PyTorch 1.12.0+; Official repo: https://github.com/snakers4/silero-vad
* type: bool, default False
* usage: --vad True

# [vad_threshold]
* description: threshold for detecting speech with Silero VAD. (Default: 0.35); low threshold reduces false positives for silence detection
* type: float, default 0.35
* usage: --vad_threshold 0.35

# [vad_onnx]
* description: whether to use ONNX for Silero VAD
* type: bool, default False
* usage: --vad_onnx True

# [min_word_dur]
* description: only allow suppressing timestamps that result in word durations greater than this value
* type: float, default 0.1
* usage: --min_word_dur 0.1

# [max_chars]
* description: maximum number of characters allowed in each segment
* type: int
* usage: --max_chars <value>

# [max_words]
* description: maximum number of words allowed in each segment
* type: int
* usage: --max_words <value>

# [demucs]
* description: whether to reprocess the audio track with Demucs to isolate vocals/remove noise; Demucs official repo: https://github.com/facebookresearch/demucs
* type: bool, default False
* usage: --demucs True

# [only_voice_freq]
* description: whether to only use sound between 200 - 5000 Hz, where the majority of human speech is.
* type: bool
* usage: --only_voice_freq True

# [strip]
* description: whether to remove spaces before and after text on each segment for output
* type: bool, default True
* usage: --strip True

# [tag]
* description: a pair of tags used to change the properties of a word at its predicted time; SRT Default: '<font color=\"#00ff00\">', '</font>'; VTT Default: '<u>', '</u>'; ASS Default: '{\\1c&HFF00&}', '{\\r}'
* type: str
* usage: --tag "<start_tag> <end_tag>"

# [reverse_text]
* description: whether to reverse the order of words for each segment of text output
* type: bool, default False
* usage: --reverse_text True

# [font]
* description: word font for ASS output(s)
* type: str, default 'Arial'
* usage: --font "<font_name>"

# [font_size]
* description: word font size for ASS output(s)
* type: int, default 48
* usage: --font_size 48

# [karaoke]
* description: whether to use progressive filling highlights for karaoke effect (only for ASS outputs)
* type: bool, default False
* usage: --karaoke True

# [temperature]
* description: temperature to use for sampling
* type: float, default 0
* usage: --temperature <value>

# [best_of]
* description: number of candidates when sampling with non-zero temperature
* type: int
* usage: --best_of <value>

# [beam_size]
* description: number of beams in beam search, only applicable when temperature is zero
* type: int
* usage: --beam_size <value>

# [patience]
* description: optional patience value to use in beam decoding, as in https://arxiv.org/abs/2204.05424, the default (1.0) is equivalent to conventional beam search
* type: float
* usage: --patience <value>

# [length_penalty]
* description: optional token length penalty coefficient (alpha) as in https://arxiv.org/abs/1609.08144, uses simple length normalization by default
* type: float
* usage: --length_penalty <value>

# [fp16]
* description: whether to perform inference in fp16; True by default
* type: bool, default True
* usage: --fp16

# [compression_ratio_threshold]
* description: if the gzip compression ratio is higher than this value, treat the decoding as failed
* type: float
* usage: --compression_ratio_threshold <value>

# [logprob_threshold]
* description: if the average log probability is lower than this value, treat the decoding as failed
* type: float
* usage: --logprob_threshold <value>

# [no_speech_threshold]
* description: if the probability of the token is higher than this value AND the decoding has failed due to `logprob_threshold`, consider the segment as silence
* type: float, default 0.6
* usage: --no_speech_threshold 0.6

# [threads]
* description: number of threads used by torch for CPU inference; supercedes MKL_NUM_THREADS/OMP_NUM_THREADS
* type: int
* usage: --threads <value>

# [mel_first]
* description: process the entire audio track into a log-Mel spectrogram first instead in chunks
* type: bool
* usage: --mel_first

# [demucs_option]
* description: Extra option(s) to use for Demucs; Replace True/False with 1/0; E.g. --demucs_option "shifts=3" --demucs_option "overlap=0.5"
* type: str
* usage: --demucs_option "<option>"

# [refine_option]
* description: Extra option(s) to use for refining timestamps; Replace True/False with 1/0; E.g. --refine_option "steps=sese" --refine_option "rel_prob_decrease=0.05"
* type: str
* usage: --refine_option "<option>"

# [model_option]
* description: Extra option(s) to use for loading the model; Replace True/False with 1/0; E.g. --model_option "in_memory=1" --model_option "cpu_threads=4"
* type: str
* usage: --model_option "<option>"

# [transcribe_option]
* description: Extra option(s) to use for transcribing/alignment; Replace True/False with 1/0; E.g. --transcribe_option "ignore_compatibility=1"
* type: str
* usage: --transcribe_option "<option>"

# [save_option]
* description: Extra option(s) to use for text outputs; Replace True/False with 1/0; E.g. --save_option "highlight_color=ffffff"
* type: str
* usage: --save_option "<option>"
        """
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
            command=lambda: self.make_open_text(hint),
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

    def make_open_text(self, texts: str):
        if not path.exists(parameters_text):
            with open(parameters_text, "w", encoding="utf-8") as f:
                f.write(texts)

        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', parameters_text))
        elif platform.system() == 'Windows':  # Windows
            startfile(parameters_text)
        else:  # linux variants
            subprocess.call(('xdg-open', parameters_text))

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
        custom_func = {"load": [load_model, load_faster_whisper], "save": [result_to_ass, result_to_srt_vtt, result_to_tsv]}
        kwargs = {"show_parsed": False}
        # transcribe is also different between whisper and faster whisper but this check should be enough

        for el in loop_for:
            if custom_func.get(el, False):
                for method in custom_func[el]:
                    res = parse_args_stable_ts(value, el, method, **kwargs)
                    if not res["success"]:
                        mbox("Invalid Stable Whisper Arguments", f"{res['msg']}", 2, self.root)
                        return
            else:
                res = parse_args_stable_ts(value, el, **kwargs)
                if not res["success"]:
                    mbox("Invalid Stable Whisper Arguments", f"{res['msg']}", 2, self.root)
                    return

        sj.save_key("whisper_args", value)
