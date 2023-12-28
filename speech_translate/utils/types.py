from typing import List, Literal, Optional, TypedDict, Union


class ToInsert(TypedDict):
    """
    Type class for inserting text to textbox
    """
    text: str
    color: Optional[str]
    is_last: Optional[bool]


class StableTsWordResult(TypedDict):
    """
    Type class for stable_ts word result (word in segment)
    """
    word: str
    start: float
    end: float
    probability: float
    tokens: List[int]
    segment_id: int
    id: int


class OriWordResult(TypedDict):
    """
    Type class for original whisper word result (word in segment)
    """
    word: str
    start: float
    end: float
    probability: float


class StableTsSegmentResult(TypedDict):
    """
    Type class for stable_ts segment result
    """
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
    """
    Type class for original whisper segment result
    """
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


class StableTsResultDict(TypedDict):
    """
    Type class for stable_ts result
    """
    text: str
    segments: List[StableTsSegmentResult]
    language: str
    time_scale: Optional[float]
    ori_dict: OriSegmentResult


class SettingDict(TypedDict):
    """
    Type class for setting.json
    """
    version: str
    checkUpdateOnStart: bool
    first_open: bool
    # ------------------ #
    # App settings
    input: Literal["mic", "speaker"]
    transcribe_mw: bool
    translate_mw: bool
    transcribe_f_import: bool
    translate_f_import: bool
    model_mw: str
    model_f_import: str
    model_f_alignment: str
    model_f_refinement: str
    source_lang_mw: str
    target_lang_mw: str
    source_lang_f_import: str
    target_lang_f_import: str
    target_lang_f_result: str
    tl_engine_mw: str
    tl_engine_f_import: str
    tl_engine_f_result: str
    verbose_record: bool
    mic: str
    speaker: str
    hostAPI: str
    separate_with: str
    theme: str
    show_audio_visualizer_in_record: bool
    show_audio_visualizer_in_setting: bool
    supress_hidden_to_tray: bool
    supress_device_warning: bool
    supress_record_warning: bool
    bypass_no_internet: bool
    mw_size: str
    sw_size: str
    dir_log: str
    dir_model: str
    auto_verify_model_on_first_setting_open: bool
    file_slice_start: str
    file_slice_end: str
    # ------------------ #
    # logging
    keep_log: bool
    log_level: str
    auto_scroll_log: bool
    auto_refresh_log: bool
    debug_realtime_record: bool
    debug_translate: bool
    debug_recorded_audio: bool
    # ------------------ #
    # Tl Settings
    https_proxy: str
    https_proxy_enable: bool
    http_proxy: str
    http_proxy_enable: bool
    supress_libre_api_key_warning: bool
    libre_api_key: str
    libre_link: str
    # ------------------ #
    # Record settings
    rec_ask_confirmation_first: bool
    # temp
    use_temp: bool
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
    threshold_auto_level_mic: int
    threshold_auto_silero_mic: bool
    threshold_silero_mic_min: float
    threshold_db_mic: float
    auto_break_buffer_mic: bool
    min_input_length_mic: float
    max_buffer_mic: int
    max_sentences_mic: int
    mic_no_limit: bool
    # speaker - device option
    sample_rate_speaker: int
    channels_speaker: str
    chunk_size_speaker: int
    auto_sample_rate_speaker: bool
    auto_channels_speaker: bool
    # speaker - record option
    threshold_enable_speaker: bool
    threshold_auto_speaker: bool
    threshold_auto_level_speaker: int
    threshold_auto_silero_speaker: bool
    threshold_silero_speaker_min: float
    threshold_db_speaker: float
    auto_break_buffer_speaker: bool
    min_input_length_speaker: float
    max_buffer_speaker: int
    max_sentences_speaker: int
    speaker_no_limit: bool
    # Transcribe settings
    dir_export: str
    auto_open_dir_export: bool
    auto_open_dir_refinement: bool
    auto_open_dir_alignment: bool
    auto_open_dir_translate: bool
    # counter hallucination
    # rec
    path_filter_rec: str
    filter_rec: bool
    filter_rec_case_sensitive: bool
    filter_rec_strip: bool
    filter_rec_ignore_punctuations: str
    filter_rec_exact_match: bool
    filter_rec_similarity: float
    # file
    path_filter_file_import: str
    filter_file_import: bool
    filter_file_import_case_sensitive: bool
    filter_file_import_strip: bool
    filter_file_import_ignore_punctuations: str
    filter_file_import_exact_match: bool
    filter_file_import_similarity: float
    remove_repetition_file_import: bool
    remove_repetition_result_refinement: bool
    remove_repetition_result_alignment: bool
    remove_repetition_amount: int
    # export
    # {file} {task} {task-short} {lang-source} {lang-target} {model} {engine}
    export_format: str
    # txt csv json srt ass vtt tsv
    export_to: List[Union[Literal["txt"], Literal["csv"], Literal["json"], Literal["srt"], Literal["ass"], Literal["vtt"],
                          Literal["tsv"]]]
    segment_max_words: str
    segment_max_chars: str
    segment_split_or_newline: Union[Literal["Split"], Literal["Newline"]]
    segment_even_split: bool
    segment_level: bool  # 1 of this must be bool
    word_level: bool  # 1 of this must be bool
    visualize_suppression: bool
    use_faster_whisper: bool
    transcribe_rate: int
    decoding_preset: str  # greedy beam search custom
    temperature: str  # 0.0 - 1.0
    best_of: Optional[int]
    beam_size: Optional[int]
    patience: Optional[float]
    compression_ratio_threshold: float
    logprob_threshold: float
    no_speech_threshold: float
    suppress_tokens: str
    initial_prompt: Optional[str]
    prefix: Optional[str]
    suppress_blank: bool
    condition_on_previous_text: bool
    max_initial_timestamp: float
    fp16: bool
    whisper_args: str
    # ------------------ #
    # Textboxes
    colorize_per_segment: bool
    colorize_per_word: bool
    gradient_low_conf: str
    gradient_high_conf: str
    # mw tc
    tb_mw_tc_auto_scroll: bool
    tb_mw_tc_limit_max: bool
    tb_mw_tc_limit_max_per_line: bool
    tb_mw_tc_max: int
    tb_mw_tc_max_per_line: int
    tb_mw_tc_font: str
    tb_mw_tc_font_bold: bool
    tb_mw_tc_font_size: int
    tb_mw_tc_use_conf_color: bool
    # mw tl
    tb_mw_tl_auto_scroll: bool
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
    tb_ex_tc_auto_scroll: bool
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
    tb_ex_tl_auto_scroll: bool
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
