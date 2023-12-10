from os import path
from tkinter import Frame, LabelFrame, Menu, StringVar, Toplevel, ttk
from typing import Literal, Union

from stable_whisper import (
    alignment,
    load_faster_whisper,
    load_model,
    result_to_ass,
    result_to_srt_vtt,
    result_to_tsv,
    whisper_word_level,
)

from speech_translate._path import p_filter_file_import, p_filter_rec, p_parameters_text
from speech_translate.linker import bc, sj
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.message import mbox
from speech_translate.ui.custom.spinbox import SpinboxNumOnly
from speech_translate.ui.custom.tooltip import CreateToolTipOnText, tk_tooltip, tk_tooltips
from speech_translate.utils.helper import change_file_w_f_call, insert_entry_readonly, popup_menu, start_file
from speech_translate.utils.whisper.helper import get_temperature, parse_args_stable_ts


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

        self.lf_decoding_options = ttk.LabelFrame(self.lf_whisper_args, text="Sampling Related")
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
        self.f_whisper_args_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_whisper_args_3 = ttk.Frame(self.lf_whisper_args)
        self.f_whisper_args_3.pack(side="top", fill="x", pady=(5, 10), padx=5)

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
            "Use faster whisper instead of whisper model.\n\nUsing faster whisper will make the" \
            "implementation up to 4 times faster than openai/whisper for the same accuracy while " \
            "using less memory. \n\nDefault is checked",
        )

        # decoding options
        self.radio_decoding_var = StringVar()
        # 1
        self.lbl_decoding_preset = ttk.Label(self.f_decoding_1, text="Decoding Preset", width=19)
        self.lbl_decoding_preset.pack(side="left", padx=5)
        self.radio_decoding_1 = ttk.Radiobutton(
            self.f_decoding_1,
            text="Greedy",
            variable=self.radio_decoding_var,
            value="greedy",
            command=lambda: self.change_decoding_preset(self.radio_decoding_var.get()),
        )
        self.radio_decoding_1.pack(side="left", padx=5)
        self.radio_decoding_2 = ttk.Radiobutton(
            self.f_decoding_1,
            text="Beam Search",
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
        self.lbl_temperature = ttk.Label(self.f_decoding_2, text="Temperature", width=19)
        self.lbl_temperature.pack(side="left", padx=5)
        self.entry_temperature = ttk.Entry(self.f_decoding_2)
        self.entry_temperature.insert(0, sj.cache["temperature"])
        self.entry_temperature.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_temperature.bind("<FocusOut>", lambda e: self.verify_temperature(self.entry_temperature.get()))
        self.entry_temperature.bind("<Return>", lambda e: self.verify_temperature(self.entry_temperature.get()))
        tk_tooltips(
            [self.lbl_temperature, self.entry_temperature],
            "Temperature for sampling. It can be a tuple of temperatures, which will be successively used upon failures " \
            "according to either `compression_ratio_threshold` or `logprob_threshold`."
        )

        # 3
        self.lbl_best_of = ttk.Label(self.f_decoding_3, text="Best of", width=19)
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
            num_float=False,
            width=25,
        )
        self.spn_best_of.pack(side="left", padx=5)
        tk_tooltips([self.lbl_best_of, self.spn_best_of], "Number of candidates when sampling with non-zero temperature")

        self.lbl_beam_size = ttk.Label(self.f_decoding_3, text="Beam size", width=15)
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
            num_float=False,
            width=25,
        )
        self.spn_beam_size.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_beam_size, self.spn_beam_size],
            "Number of beams in beam search, only applicable when temperature is zero"
        )

        self.lbl_patience = ttk.Label(self.f_decoding_3, text="Patience", width=19)
        self.lbl_patience.pack(side="left", padx=5)
        self.spn_patience = SpinboxNumOnly(
            self.root,
            self.f_decoding_3,
            -100,
            100,
            lambda x: sj.save_key("patience",
                                  float(x) if x != "" else None),
            initial_value=sj.cache["patience"],
            allow_empty=True,
            num_float=True,
            width=25,
        )
        self.spn_patience.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_patience, self.spn_patience],
            "Optional patience value to use in beam decoding, as in https://arxiv.org/abs/2204.05424, " \
            "value of 1.0 is equivalent to conventional beam search"
        )

        # threshold
        self.lbl_compression_ratio_threshold = ttk.Label(self.f_threshold_1, text="Compression Ratio", width=19)
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
        tk_tooltips(
            [self.lbl_compression_ratio_threshold, self.spn_compression_ratio_threshold],
            "if the gzip compression ratio is higher than this value, treat the decoding as failed"
        )

        self.lbl_logprob_threshold = ttk.Label(self.f_threshold_1, text="Logprob", width=15)
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
        tk_tooltips(
            [self.lbl_logprob_threshold, self.spn_logprob_threshold],
            "if the average log probability is lower than this value, treat the decoding as failed"
        )

        self.lbl_no_speech_threshold = ttk.Label(self.f_threshold_1, text="No Speech", width=15)
        self.lbl_no_speech_threshold.pack(side="left", padx=5)
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
        tk_tooltips(
            [self.lbl_no_speech_threshold, self.spn_no_speech_threshold],
            "if the probability of the <|nospeech|> token is higher than this value AND the decoding " \
            "has failed due to `logprob_threshold`, consider the segment as silence"
        )

        # other whisper args
        self.lbl_initial_prompt = ttk.Label(self.f_whisper_args_1, text="Initial Prompt", width=19)
        self.lbl_initial_prompt.pack(side="left", padx=5)
        self.entry_initial_prompt = ttk.Entry(self.f_whisper_args_1, width=30)
        self.entry_initial_prompt.insert(0, sj.cache["initial_prompt"] or "")
        self.entry_initial_prompt.pack(side="left", padx=5, fill="x")
        self.entry_initial_prompt.bind(
            "<KeyRelease>", lambda e: sj.save_key(
                "initial_prompt",
                self.entry_initial_prompt.get() if len(self.entry_initial_prompt.get()) > 0 else None
            )
        )
        tk_tooltips(
            [self.lbl_initial_prompt, self.entry_initial_prompt],
            "optional text to provide as a prompt for the first window.\n\nDefault is empty",
        )

        self.lbl_prefix = ttk.Label(self.f_whisper_args_1, text="Prefix", width=15)
        self.lbl_prefix.pack(side="left", padx=5)
        self.entry_prefix = ttk.Entry(self.f_whisper_args_1, width=30)
        self.entry_prefix.insert(0, sj.cache["prefix"] or "")
        self.entry_prefix.pack(side="left", padx=5, fill="x")
        self.entry_prefix.bind(
            "<KeyRelease>",
            lambda e: sj.save_key("prefix",
                                  self.entry_prefix.get() if len(self.entry_prefix.get()) > 0 else None)
        )
        tk_tooltips(
            [self.lbl_prefix, self.entry_prefix],
            "Optional text to prefix the current context.\n\nDefault is empty",
        )

        self.lbl_suppress_tokens = ttk.Label(self.f_whisper_args_1, text="Supress Token", width=15)
        self.lbl_suppress_tokens.pack(side="left", padx=5)
        self.entry_supress_tokens = ttk.Entry(self.f_whisper_args_1, width=30)
        self.entry_supress_tokens.pack(side="left", padx=5, fill="x")
        self.entry_supress_tokens.insert(0, sj.cache["suppress_tokens"])
        self.entry_supress_tokens.bind(
            "<KeyRelease>", lambda e: sj.save_key("suppress_tokens", self.entry_supress_tokens.get())
        )
        tk_tooltips(
            [self.lbl_suppress_tokens, self.entry_supress_tokens],
            "Comma-separated list of token ids to suppress during sampling;"
            " '-1' will suppress most special characters except common punctuations.\n\nDefault is empty",
        )

        self.lbl_max_initial_timestamp = ttk.Label(self.f_whisper_args_2, text="Max Initial Timestamp", width=19)
        self.lbl_max_initial_timestamp.pack(side="left", padx=5)
        self.spn_max_initial_timestamp = SpinboxNumOnly(
            self.root,
            self.f_whisper_args_2,
            0,
            100,
            lambda x: sj.save_key("max_initial_timestamp",
                                  float(x) if x != "" else None),
            initial_value=sj.cache["max_initial_timestamp"],
            allow_empty=True,
            num_float=True,
            width=25,
        )
        self.spn_max_initial_timestamp.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_max_initial_timestamp, self.spn_max_initial_timestamp],
            "Maximum initial timestamp to use for the first window\n\nDefault is empty",
        )

        self.cbtn_suppress_blank = CustomCheckButton(
            self.f_whisper_args_2,
            sj.cache["suppress_blank"],
            lambda x: sj.save_key("suppress_blank", x),
            text="Suppress Blank",
            style="Switch.TCheckbutton",
        )
        self.cbtn_suppress_blank.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_suppress_blank,
            "if True, will suppress blank outputs. Default is true/checked",
        )

        self.cbtn_condition_on_previous_text = CustomCheckButton(
            self.f_whisper_args_2,
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

        self.cbtn_fp16 = CustomCheckButton(
            self.f_whisper_args_2,
            sj.cache["fp16"],
            lambda x: sj.save_key("fp16", x),
            text="FP16",
            style="Switch.TCheckbutton",
        )
        self.cbtn_fp16.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_fp16,
            "if True, will use fp16 for inference. Default is true/checked",
        )

        # 3
        self.lbl_whisper_args = ttk.Label(self.f_whisper_args_3, text="Raw Arguments", width=19)
        self.lbl_whisper_args.pack(side="left", padx=5)
        self.entry_whisper_args = ttk.Entry(self.f_whisper_args_3)
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

# [demucs]
* description: whether to reprocess the audio track with Demucs to isolate vocals/remove noise; Demucs official repo: https://github.com/facebookresearch/demucs
* type: bool, default False
* usage: --demucs True

# [demucs_output]
* path(s) to save the vocals isolated by Demucs as WAV file(s); ignored if [demucs]=False
* type: str
* usage: --demucs_output "<path>"

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
            self.f_whisper_args_3,
            image=bc.question_emoji,
            command=lambda: self.make_open_text(hint),
            width=5,
        )
        self.btn_help.pack(side="left", padx=5)
        tk_tooltip(self.btn_help, "Click to see the available arguments.")

        # ----------------------------------
        self.lf_fltr_hallucination = LabelFrame(self.master, text="• Filter Hallucination")
        self.lf_fltr_hallucination.pack(side="top", fill="x", pady=5, padx=5)

        self.f_fltr_hallucination_1 = ttk.Frame(self.lf_fltr_hallucination)
        self.f_fltr_hallucination_1.pack(side="top", fill="x", padx=5)

        self.f_fltr_hallucination_1_l = ttk.Frame(self.lf_fltr_hallucination)
        self.f_fltr_hallucination_1_l.pack(side="left", fill="both", expand=True)

        self.f_fltr_hallucination_1_r = ttk.Frame(self.lf_fltr_hallucination)
        self.f_fltr_hallucination_1_r.pack(side="left", fill="both", expand=True)

        # rec
        self.lf_fltr_rec = ttk.LabelFrame(self.f_fltr_hallucination_1_l, text="• Filter Record")
        self.lf_fltr_rec.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        self.f_fltr_rec_1 = ttk.Frame(self.lf_fltr_rec)
        self.f_fltr_rec_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_fltr_rec_2 = ttk.Frame(self.lf_fltr_rec)
        self.f_fltr_rec_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_fltr_rec_3 = ttk.Frame(self.lf_fltr_rec)
        self.f_fltr_rec_3.pack(side="top", fill="x", pady=5, padx=5)

        self.cbtn_fltr_rec = CustomCheckButton(
            self.f_fltr_rec_1,
            sj.cache["filter_rec"],
            lambda x: sj.save_key("filter_rec", x),
            text="Filter Record",
            style="Switch.TCheckbutton",
        )
        self.cbtn_fltr_rec.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_fltr_rec,
            "Filter hallucination in record using provided filter file."
            "\n\nThe filter works by checking if there is any segment that match any of the string provided "
            "in the filter list based on each language.\n\nDefault is checked",
        )

        self.lbl_fltr_rec = ttk.Label(self.f_fltr_rec_2, text="Filter Path", width=19)
        self.lbl_fltr_rec.pack(side="left", padx=5)
        self.entry_fltr_rec = ttk.Entry(self.f_fltr_rec_2)
        insert_entry_readonly(
            self.entry_fltr_rec, sj.cache["path_filter_rec"] if sj.cache["path_filter_rec"] != "auto" else p_filter_rec
        )
        self.entry_fltr_rec.pack(side="left", fill="x", expand=True, padx=5)
        tk_tooltips(
            [self.lbl_fltr_rec, self.entry_fltr_rec],
            "Path to filter file containing lists of words for all language of Whisper in that is usually generated " \
            "by the model when it hallucinate because of noises.",
            wrap_len=300,
        )

        self.btn_fltr_rec_config = ttk.Button(
            self.f_fltr_rec_2,
            image=bc.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_fltr_rec),
        )
        self.btn_fltr_rec_config.pack(side="left", padx=5)

        def confirm_reset(title, element, key, value):
            if mbox(title, "Are you sure you want to reset the filter to its default path?", 3, self.root):
                insert_entry_readonly(element, value)
                sj.save_key(key, "auto")

        self.menu_fltr_rec = Menu(self.master, tearoff=0)
        self.menu_fltr_rec.add_command(
            label="Open/Edit Filter File",
            image=bc.open_emoji,
            compound="left",
            command=lambda: start_file(self.entry_fltr_rec.get())
        )
        self.menu_fltr_rec.add_separator()
        self.menu_fltr_rec.add_command(
            label="Change Filter File",
            compound="left",
            image=bc.folder_emoji,
            command=lambda: change_file_w_f_call(
                self.entry_fltr_rec, lambda v: sj.save_key("path_filter_rec", v), "Change Filter File",
                (("JSON (Filter file)", "*.json"), ), self.root
            )
        )
        self.menu_fltr_rec.add_command(
            label="Set back to Default Filter File",
            compound="left",
            image=bc.reset_emoji,
            command=lambda: confirm_reset("Reset Filter File", self.entry_fltr_rec, "path_filter_rec", p_filter_rec),
        )

        self.lbl_ignore_punctuations = ttk.Label(self.f_fltr_rec_3, text="Ignore Punctuations", width=19)
        self.lbl_ignore_punctuations.pack(side="left", padx=5)

        self.entry_ignore_punctuations = ttk.Entry(self.f_fltr_rec_3)
        self.entry_ignore_punctuations.insert(0, sj.cache["filter_rec_ignore_punctuations"])
        self.entry_ignore_punctuations.pack(side="left", fill="x", expand=False, padx=5)
        self.entry_ignore_punctuations.bind(
            "<KeyRelease>",
            lambda e: sj.save_key("filter_rec_ignore_punctuations",
                                  self.entry_ignore_punctuations.get().strip())
        )
        tk_tooltips(
            [self.lbl_ignore_punctuations, self.entry_ignore_punctuations],
            "Punctuations to ignore when filtering hallucination in record.\n\nDefault is \"',.?!",
        )

        self.cbtn_filter_rec_strip = CustomCheckButton(
            self.f_fltr_rec_3,
            sj.cache["filter_rec_strip"],
            lambda x: sj.save_key("filter_rec_strip", x),
            text="Strip",
            style="Switch.TCheckbutton",
        )
        self.cbtn_filter_rec_strip.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_filter_rec_strip,
            "Whether to ignore spaces before and after each string.\n\nDefault is checked",
        )

        self.cbtn_fltr_rec_case_sensitive = CustomCheckButton(
            self.f_fltr_rec_3,
            sj.cache["filter_rec_case_sensitive"],
            lambda x: sj.save_key("filter_rec_case_sensitive", x),
            text="Case Sensitive",
            style="Switch.TCheckbutton",
        )
        self.cbtn_fltr_rec_case_sensitive.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_fltr_rec_case_sensitive,
            "Whether the case of the string need to match to be removed\n\nDefault is unchecked",
        )

        # File import
        self.lf_fltr_file_import = ttk.LabelFrame(self.f_fltr_hallucination_1_r, text="• Filter File Import")
        self.lf_fltr_file_import.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        self.f_fltr_file_import_1 = ttk.Frame(self.lf_fltr_file_import)
        self.f_fltr_file_import_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_fltr_file_import_2 = ttk.Frame(self.lf_fltr_file_import)
        self.f_fltr_file_import_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_fltr_file_import_3 = ttk.Frame(self.lf_fltr_file_import)
        self.f_fltr_file_import_3.pack(side="top", fill="x", pady=5, padx=5)

        self.cbtn_filter_file_import = CustomCheckButton(
            self.f_fltr_file_import_1,
            sj.cache["filter_file_import"],
            lambda x: sj.save_key("filter_file_import", x),
            text="Filter File Import",
            style="Switch.TCheckbutton",
        )
        self.cbtn_filter_file_import.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_filter_file_import,
            "Filter hallucination in file import using provided filter file."
            "\n\nThe filter works by checking if there is any segment that match any of the string provided "
            "in the filter list based on each language."
            "\n\nEnabling filter on file import will not make it filter the result in align and refine result mode"
            "\n\nDefault is checked",
            wrap_len=300,
        )

        self.lbl_fltr_file_import = ttk.Label(self.f_fltr_file_import_2, text="Filter Path", width=19)
        self.lbl_fltr_file_import.pack(side="left", padx=5)

        self.entry_fltr_file_import = ttk.Entry(self.f_fltr_file_import_2)
        insert_entry_readonly(
            self.entry_fltr_file_import,
            sj.cache["path_filter_file_import"] if sj.cache["path_filter_file_import"] != "auto" else p_filter_file_import
        )
        self.entry_fltr_file_import.pack(side="left", fill="x", expand=True, padx=5)
        tk_tooltips(
            [self.lbl_fltr_file_import, self.entry_fltr_file_import],
            "Path to filter file containing lists of words for all language of Whisper in that is usually generated " \
            "by the model when it hallucinate because of noises.",
            wrap_len=300,
        )

        self.btn_fltr_file_import_config = ttk.Button(
            self.f_fltr_file_import_2,
            image=bc.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_fltr_file_import),
        )
        self.btn_fltr_file_import_config.pack(side="left", padx=5)

        self.menu_fltr_file_import = Menu(self.master, tearoff=0)
        self.menu_fltr_file_import.add_command(
            label="Open/Edit Filter File",
            image=bc.open_emoji,
            compound="left",
            command=lambda: start_file(self.entry_fltr_file_import.get())
        )
        self.menu_fltr_file_import.add_separator()
        self.menu_fltr_file_import.add_command(
            label="Change Filter File",
            image=bc.folder_emoji,
            compound="left",
            command=lambda: change_file_w_f_call(
                self.entry_fltr_file_import, lambda v: sj.save_key("path_filter_file_import", v), "Change Filter File",
                (("JSON (Filter file)", "*.json"), ), self.root
            ),
        )
        self.menu_fltr_file_import.add_command(
            label="Set back to Default Filter File",
            image=bc.reset_emoji,
            compound="left",
            command=lambda:
            confirm_reset("Reset Filter File", self.entry_fltr_file_import, "path_filter_file_import", p_filter_file_import),
        )

        self.lbl_ignore_punctuations_file_import = ttk.Label(self.f_fltr_file_import_3, text="Ignore Punctuations", width=19)
        self.lbl_ignore_punctuations_file_import.pack(side="left", padx=5)
        self.entry_ignore_punctuations_file_import = ttk.Entry(self.f_fltr_file_import_3)
        self.entry_ignore_punctuations_file_import.insert(0, sj.cache["filter_file_import_ignore_punctuations"])
        self.entry_ignore_punctuations_file_import.pack(side="left", fill="x", expand=False, padx=5)
        self.entry_ignore_punctuations_file_import.bind(
            "<KeyRelease>", lambda e: sj.
            save_key("filter_file_import_ignore_punctuations",
                     self.entry_ignore_punctuations_file_import.get().strip())
        )
        tk_tooltips(
            [self.lbl_ignore_punctuations_file_import, self.entry_ignore_punctuations_file_import],
            "Punctuations to ignore when filtering hallucination in file import.\n\nDefault is \"',.?!",
        )

        self.cbtn_filter_file_import_strip = CustomCheckButton(
            self.f_fltr_file_import_3,
            sj.cache["filter_file_import_strip"],
            lambda x: sj.save_key("filter_file_import_strip", x),
            text="Strip",
            style="Switch.TCheckbutton",
        )
        self.cbtn_filter_file_import_strip.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_filter_file_import_strip,
            "Whether to ignore spaces before and after each string.\n\nDefault is checked",
        )

        self.cbtn_fltr_file_import_case_sensitive = CustomCheckButton(
            self.f_fltr_file_import_3,
            sj.cache["filter_file_import_case_sensitive"],
            lambda x: sj.save_key("filter_file_import_case_sensitive", x),
            text="Case Sensitive",
            style="Switch.TCheckbutton",
        )
        self.cbtn_fltr_file_import_case_sensitive.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_fltr_file_import_case_sensitive,
            "Whether the case of the string need to match to be removed\n\nDefault is unchecked",
        )

        # --------------------------
        self.__init_setting_once()

    # ------------------ Functions ------------------
    def __init_setting_once(self):
        self.change_decoding_preset(sj.cache["decoding_preset"])

    def change_decoding_preset(self, value: str):
        self.radio_decoding_var.set(value)
        sj.save_key("decoding_preset", value)
        if value == "custom":
            self.entry_temperature.configure(state="normal")
            self.spn_best_of.configure(state="normal")
            self.spn_beam_size.configure(state="normal")
            self.spn_patience.configure(state="normal")
        else:
            self.entry_temperature.configure(state="disabled")
            self.spn_best_of.configure(state="disabled")
            self.spn_beam_size.configure(state="disabled")
            self.spn_patience.configure(state="disabled")

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

                self.spn_patience.set("")
                sj.save_key("patience", None)

            elif value == "beam search":
                self.entry_temperature.configure(state="normal")
                self.entry_temperature.delete(0, "end")
                self.entry_temperature.insert(0, "0.0, 0.2, 0.4, 0.6, 0.8, 1.0")
                self.entry_temperature.configure(state="disabled")
                sj.save_key("temperature", "0.0, 0.2, 0.4, 0.6, 0.8, 1.0")

                self.spn_best_of.set(3)
                sj.save_key("best_of", 3)

                self.spn_beam_size.set(3)
                sj.save_key("beam_size", 3)

                self.spn_patience.set(1.0)
                sj.save_key("patience", 1.0)

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

    def make_open_text(self, texts: str):
        if not path.exists(p_parameters_text):
            with open(p_parameters_text, "w", encoding="utf-8") as f:
                f.write(texts)

        start_file(p_parameters_text)

    def verify_temperature(self, value: str):
        status, msg = get_temperature(value)
        if not status:
            self.entry_temperature.delete(0, "end")
            self.entry_temperature.insert(0, sj.cache["temperature"])
            mbox("Invalid Temperature Options", f"{msg}", 2, self.root)

            return

        sj.save_key("temperature", value)

    def verify_raw_args(self, value: str):
        loop_for = ["load", "transcribe", "align", "refine", "save"]
        custom_func = {
            "load": [load_model, load_faster_whisper],
            "transcribe": [whisper_word_level.transcribe_stable],
            "save": [result_to_ass, result_to_srt_vtt, result_to_tsv],
            "align": [alignment.align],
            "refine": [alignment.refine]
        }
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
