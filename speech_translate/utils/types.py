from dataclasses import dataclass
from typing import Literal, Optional, TypedDict, List, Union


class ToInsert(TypedDict):
    text: str
    color: Optional[str]
    is_last: Optional[bool]


class StableTsWordResult(TypedDict):
    word: str
    start: float
    end: float
    probability: float
    tokens: List[int]
    segment_id: int
    id: int


class OriWordResult(TypedDict):
    word: str
    start: float
    end: float
    probability: float


class StableTsSegmentResult(TypedDict):
    start: float
    end: float
    text: str
    seek: int
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: List[StableTsWordResult]
    id: int


class OriSegmentResult(TypedDict):
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: List[OriWordResult]


@dataclass
class StableTsResultDict(TypedDict):
    text: str
    segments: List[StableTsSegmentResult]
    language: str
    time_scale: Optional[float]
    ori_dict: OriSegmentResult


class SettingDict(TypedDict):
    version: str
    checkUpdateOnStart: bool
    first_open: bool
    # ------------------ #
    # App settings
    transcribe: bool
    translate: bool
    input: Literal["mic", "speaker"]
    model: str
    verbose: bool
    separate_with: str
    mic: str
    speaker: str
    hostAPI: str
    theme: str
    supress_hidden_to_tray: bool
    supress_device_warning: bool
    mw_size: str
    sw_size: str
    dir_log: str
    dir_model: str
    file_slice_start: str
    file_slice_end: str
    parse_arabic: bool
    # ------------------ #
    # logging
    keep_log: bool
    log_level: str
    auto_scroll_log: bool
    auto_refresh_log: bool
    ignore_stdout: List[str]
    debug_realtime_record: bool
    debug_translate: bool
    # ------------------ #
    # Tl Settings
    sourceLang: str
    targetLang: str
    tl_engine: str
    https_proxy: str
    https_proxy_enable: bool
    http_proxy: str
    http_proxy_enable: bool
    supress_libre_api_key_warning: bool
    libre_api_key: str
    libre_host: str
    libre_port: str
    libre_https: bool
    # ------------------ #
    # Record settings
    debug_recorded_audio: bool
    # temp
    use_temp: bool
    max_temp: int
    keep_temp: bool
    # mic - device option
    sample_rate_mic: int
    channels_mic: str  # Mono, Stereo, custom -> "1", "2", ...
    chunk_size_mic: int
    auto_sample_rate_mic: bool
    auto_channels_mic: bool
    # mic - record option
    threshold_enable_mic: bool
    threshold_auto_mic: bool
    threshold_auto_mode_mic: int
    threshold_db_mic: float
    auto_break_buffer_mic: bool
    max_buffer_mic: int
    max_sentences_mic: int
    # speaker - device option
    sample_rate_speaker: int
    channels_speaker: str
    chunk_size_speaker: int
    auto_sample_rate_speaker: bool
    auto_channels_speaker: bool
    # speaker - record option
    threshold_enable_speaker: bool
    threshold_auto_speaker: bool
    threshold_auto_mode_speaker: int
    threshold_db_speaker: float
    auto_break_buffer_speaker: bool
    max_buffer_speaker: int
    max_sentences_speaker: int
    # Transcribe settings
    dir_export: str
    auto_open_dir_export: bool
    auto_open_dir_refinement: bool
    auto_open_dir_alignment: bool
    auto_open_dir_translate: bool
    # {file} {task} {task-short} {lang-source} {lang-target} {model} {engine}
    export_format: str
    # txt csv json srt ass vtt tsv
    export_to: List[Union[Literal["txt"], Literal["csv"], Literal["json"], Literal["srt"], Literal["ass"], Literal["vtt"],
                          Literal["tsv"]]]
    segment_level: bool  # 1 of this must be bool
    word_level: bool  # 1 of this must be bool
    visualize_suppression: bool
    use_faster_whisper: bool
    transcribe_rate: int
    decoding_preset: str  # greedy beam search custom
    temperature: str  # 0.0 - 1.0
    best_of: int
    beam_size: int
    compression_ratio_threshold: float
    logprob_threshold: float
    no_speech_threshold: float
    suppress_tokens: str
    initial_prompt: str
    condition_on_previous_text: bool
    whisper_args: str
    # ------------------ #
    # Textboxes
    colorize_per_segment: bool
    colorize_per_word: bool
    gradient_low_conf: str
    gradient_high_conf: str
    # mw tc
    tb_mw_tc_limit_max: bool
    tb_mw_tc_limit_max_per_line: bool
    tb_mw_tc_max: int
    tb_mw_tc_max_per_line: int
    tb_mw_tc_font: str
    tb_mw_tc_font_bold: bool
    tb_mw_tc_font_size: int
    tb_mw_tc_use_conf_color: bool
    # mw tl
    tb_mw_tl_limit_max: bool
    tb_mw_tl_limit_max_per_line: bool
    tb_mw_tl_max: int
    tb_mw_tl_max_per_line: int
    tb_mw_tl_font: str
    tb_mw_tl_font_bold: bool
    tb_mw_tl_font_size: int
    tb_mw_tl_use_conf_color: bool
    # Tc sub
    ex_tc_geometry: str
    ex_tc_always_on_top: Literal[0, 1]
    ex_tc_click_through: Literal[0, 1]
    ex_tc_no_title_bar: Literal[0, 1]
    ex_tc_no_tooltip: Literal[0, 1]
    tb_ex_tc_limit_max: bool
    tb_ex_tc_limit_max_per_line: bool
    tb_ex_tc_max: int
    tb_ex_tc_max_per_line: int
    tb_ex_tc_font: str
    tb_ex_tc_font_bold: bool
    tb_ex_tc_font_size: int
    tb_ex_tc_font_color: str
    tb_ex_tc_bg_color: str
    tb_ex_tc_use_conf_color: bool
    # Tl sub
    ex_tl_geometry: str
    ex_tl_always_on_top: Literal[0, 1]
    ex_tl_click_through: Literal[0, 1]
    ex_tl_no_title_bar: Literal[0, 1]
    ex_tl_no_tooltip: Literal[0, 1]
    tb_ex_tl_limit_max: bool
    tb_ex_tl_limit_max_per_line: bool
    tb_ex_tl_max: int
    tb_ex_tl_max_per_line: int
    tb_ex_tl_font: str
    tb_ex_tl_font_bold: bool
    tb_ex_tl_font_size: int
    tb_ex_tl_font_color: str
    tb_ex_tl_bg_color: str
    tb_ex_tl_use_conf_color: bool
