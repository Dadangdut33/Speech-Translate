from speech_translate.ui.frame.setting import export
from speech_translate.ui.frame.setting import general
from speech_translate.ui.frame.setting import record
from speech_translate.ui.frame.setting import textbox
from speech_translate.ui.frame.setting import transcribe
from speech_translate.ui.frame.setting import translate

from speech_translate.ui.frame.setting.export import (SettingExport,)
from speech_translate.ui.frame.setting.general import (ModelDownloadFrame,
                                                       SettingGeneral,)
from speech_translate.ui.frame.setting.record import (RecordingOptionsDevice,
                                                      SettingRecord,)
from speech_translate.ui.frame.setting.textbox import (BaseTbSetting,
                                                       SettingTextbox,)
from speech_translate.ui.frame.setting.transcribe import (SettingTranscribe,)
from speech_translate.ui.frame.setting.translate import (SettingTranslate,)

__all__ = ['BaseTbSetting', 'ModelDownloadFrame', 'RecordingOptionsDevice',
           'SettingExport', 'SettingGeneral', 'SettingRecord',
           'SettingTextbox', 'SettingTranscribe', 'SettingTranslate', 'export',
           'general', 'record', 'textbox', 'transcribe', 'translate']

from speech_translate.utils.whisper import download
from speech_translate.utils.whisper import helper
from speech_translate.utils.whisper import load
from speech_translate.utils.whisper import result
from speech_translate.utils.whisper import save

from speech_translate.utils.whisper.download import (download_model,
                                                     get_default_download_root,
                                                     verify_model_faster_whisper,
                                                     verify_model_whisper,)
from speech_translate.utils.whisper.helper import (append_dot_en,
                                                   create_hallucination_filter,
                                                   get_base_filter,
                                                   get_hallucination_filter,
                                                   get_task_format,
                                                   get_temperature, model_keys,
                                                   model_select_dict,
                                                   model_values,
                                                   stablets_verbose_log,
                                                   to_language_name,)
from speech_translate.utils.whisper.load import (ArgumentParserWithErrors,
                                                 get_model, get_model_args,
                                                 get_tc_args, optional_float,
                                                 optional_int,
                                                 parse_args_stable_ts,
                                                 str2bool, str2val,)
from speech_translate.utils.whisper.result import (remove_segments_by_str,
                                                   split_res,)
from speech_translate.utils.whisper.save import (fname_dupe_check,
                                                 save_output_stable_ts,
                                                 write_csv,)

__all__ = ['ArgumentParserWithErrors', 'append_dot_en',
           'create_hallucination_filter', 'download', 'download_model',
           'fname_dupe_check', 'get_base_filter', 'get_default_download_root',
           'get_hallucination_filter', 'get_model', 'get_model_args',
           'get_task_format', 'get_tc_args', 'get_temperature', 'helper',
           'load', 'model_keys', 'model_select_dict', 'model_values',
           'optional_float', 'optional_int', 'parse_args_stable_ts',
           'remove_segments_by_str', 'result', 'save', 'save_output_stable_ts',
           'split_res', 'stablets_verbose_log', 'str2bool', 'str2val',
           'to_language_name', 'verify_model_faster_whisper',
           'verify_model_whisper', 'write_csv']

from speech_translate.utils.translate import language
from speech_translate.utils.translate import translator

from speech_translate.utils.translate.language import (GOOGLE_KEY_VAL,
                                                       GOOGLE_LIST_UPPED,
                                                       GOOGLE_SOURCE,
                                                       GOOGLE_TARGET,
                                                       GOOGLE_WHISPER_COMPATIBLE,
                                                       LANGUAGES,
                                                       LIBRE_KEY_VAL,
                                                       LIBRE_LIST_UPPED,
                                                       LIBRE_SOURCE,
                                                       LIBRE_TARGET,
                                                       LIBRE_WHISPER_COMPATIBLE,
                                                       MYMEMORY_KEY_VAL,
                                                       MYMEMORY_SOURCE,
                                                       MYMEMORY_WHISPER_COMPATIBLE,
                                                       MY_MEMORY_TARGET,
                                                       TL_ENGINE_SOURCE_DICT,
                                                       TL_ENGINE_TARGET_DICT,
                                                       TO_LANGUAGE_CODE,
                                                       WHISPER_CODE_TO_NAME,
                                                       WHISPER_LANG_LIST,
                                                       WHISPER_LIST_UPPED,
                                                       WHISPER_SOURCE,
                                                       WHISPER_SOURCE_V3,
                                                       WHISPER_TARGET,
                                                       get_whisper_lang_name,
                                                       get_whisper_lang_similar,
                                                       get_whisper_lang_source,
                                                       is_it_there, to_remove,
                                                       verify_language_in_key,)
from speech_translate.utils.translate.translator import (TlCon,
    TranslationConnection, google_tl, libre_tl, memory_tl, tl_batch_with_tqdm,
    tl_dict, translate,)

__all__ = ['GOOGLE_KEY_VAL', 'GOOGLE_LIST_UPPED', 'GOOGLE_SOURCE',
           'GOOGLE_TARGET', 'GOOGLE_WHISPER_COMPATIBLE', 'LANGUAGES',
           'LIBRE_KEY_VAL', 'LIBRE_LIST_UPPED', 'LIBRE_SOURCE', 'LIBRE_TARGET',
           'LIBRE_WHISPER_COMPATIBLE', 'MYMEMORY_KEY_VAL', 'MYMEMORY_SOURCE',
           'MYMEMORY_WHISPER_COMPATIBLE', 'MY_MEMORY_TARGET',
           'TL_ENGINE_SOURCE_DICT', 'TL_ENGINE_TARGET_DICT',
           'TO_LANGUAGE_CODE', 'TlCon', 'TranslationConnection',
           'WHISPER_CODE_TO_NAME', 'WHISPER_LANG_LIST', 'WHISPER_LIST_UPPED',
           'WHISPER_SOURCE', 'WHISPER_SOURCE_V3', 'WHISPER_TARGET',
           'get_whisper_lang_name', 'get_whisper_lang_similar',
           'get_whisper_lang_source', 'google_tl', 'is_it_there', 'language',
           'libre_tl', 'memory_tl', 'tl_batch_with_tqdm', 'tl_dict',
           'to_remove', 'translate', 'translator', 'verify_language_in_key']

from speech_translate.utils.tk import style

from speech_translate.utils.tk.style import (get_current_theme, get_root,
                                             get_style, get_theme_list,
                                             init_theme, set_theme,
                                             set_ui_style, theme_list,)

__all__ = ['get_current_theme', 'get_root', 'get_style', 'get_theme_list',
           'init_theme', 'set_theme', 'set_ui_style', 'style', 'theme_list']

from speech_translate.utils.custom import queue

from speech_translate.utils.custom.queue import (MyQueue, SharedCounter,)

__all__ = ['MyQueue', 'SharedCounter', 'queue']

from speech_translate.utils.audio import audio
from speech_translate.utils.audio import beep
from speech_translate.utils.audio import device
from speech_translate.utils.audio import file
from speech_translate.utils.audio import record

from speech_translate.utils.audio.audio import (Frame, frame_generator, get_db,
                                                get_frame_duration,
                                                get_speech_webrtc, resample_sr,
                                                to_silero,)
from speech_translate.utils.audio.beep import (beep,)
from speech_translate.utils.audio.device import (get_channel_int,
                                                 get_default_host_api,
                                                 get_default_input_device,
                                                 get_default_output_device,
                                                 get_device_details,
                                                 get_host_apis,
                                                 get_input_devices,
                                                 get_output_devices,)
from speech_translate.utils.audio.file import (F_IMPORT_COUNTER,
                                               cancellable_tc, cancellable_tl,
                                               mod_result, process_file,
                                               processed_tc, processed_tl,
                                               run_translate_api, run_whisper,
                                               translate_result,
                                               update_q_process,)
from speech_translate.utils.audio.record import (ERROR_CON_NOFIFIED_AMOUNT,
                                                 ERROR_CON_NOTIFIED, record_cb,
                                                 record_session,
                                                 run_whisper_tl, tl_api,)

__all__ = ['ERROR_CON_NOFIFIED_AMOUNT', 'ERROR_CON_NOTIFIED',
           'F_IMPORT_COUNTER', 'Frame', 'audio', 'beep', 'cancellable_tc',
           'cancellable_tl', 'device', 'file', 'frame_generator',
           'get_channel_int', 'get_db', 'get_default_host_api',
           'get_default_input_device', 'get_default_output_device',
           'get_device_details', 'get_frame_duration', 'get_host_apis',
           'get_input_devices', 'get_output_devices', 'get_speech_webrtc',
           'mod_result', 'process_file', 'processed_tc', 'processed_tl',
           'record', 'record_cb', 'record_session', 'resample_sr',
           'run_translate_api', 'run_whisper', 'run_whisper_tl', 'tl_api',
           'to_silero', 'translate_result', 'update_q_process']

from speech_translate.ui.window import about
from speech_translate.ui.window import log
from speech_translate.ui.window import main
from speech_translate.ui.window import setting
from speech_translate.ui.window import transcribed
from speech_translate.ui.window import translated

from speech_translate.ui.window.about import (AboutWindow,)
from speech_translate.ui.window.log import (LogWindow,)
from speech_translate.ui.window.main import (AppTray, MainWindow,
                                             NoConsolePopen,
                                             add_ffmpeg_to_path,
                                             check_cuda_and_gpu, get_gpu_info,
                                             main, signal_handler,)
from speech_translate.ui.window.setting import (SettingWindow,)
from speech_translate.ui.window.transcribed import (TcsWindow,)
from speech_translate.ui.window.translated import (TlsWindow,)

__all__ = ['AboutWindow', 'AppTray', 'LogWindow', 'MainWindow',
           'NoConsolePopen', 'SettingWindow', 'TcsWindow', 'TlsWindow',
           'about', 'add_ffmpeg_to_path', 'check_cuda_and_gpu', 'get_gpu_info',
           'log', 'main', 'setting', 'signal_handler', 'transcribed',
           'translated']

from speech_translate.ui.template import detached

from speech_translate.ui.template.detached import (SubtitleWindow,)

__all__ = ['SubtitleWindow', 'detached']

from speech_translate.ui.frame import setting

__all__ = ['setting']

from speech_translate.ui.custom import audio
from speech_translate.ui.custom import checkbutton
from speech_translate.ui.custom import combobox
from speech_translate.ui.custom import dialog
from speech_translate.ui.custom import download
from speech_translate.ui.custom import label
from speech_translate.ui.custom import message
from speech_translate.ui.custom import spinbox
from speech_translate.ui.custom import tooltip

from speech_translate.ui.custom.audio import (AudioMeter,)
from speech_translate.ui.custom.checkbutton import (CustomCheckButton,)
from speech_translate.ui.custom.combobox import (CB_NAV_KEY_SCRIPT,
                                                 CategorizedComboBox,
                                                 ComboboxTypeOnCustom,
                                                 ComboboxWithKeyNav,)
from speech_translate.ui.custom.dialog import (AlignmentDialog,
                                               FileImportDialog,
                                               FileOperationDialog,
                                               FileProcessDialog,
                                               ModResultInputDialog,
                                               MultipleChoiceQuestion,
                                               QueueDialog, RefinementDialog,
                                               TranslateResultDialog,
                                               prompt_with_choices,)
from speech_translate.ui.custom.download import (
                                                 faster_whisper_download_with_progress_gui,
                                                 snapshot_download,
                                                 whisper_download_with_progress_gui,)
from speech_translate.ui.custom.label import (DraggableHtmlLabel,
                                              LabelTitleText,)
from speech_translate.ui.custom.message import (MBoxText, mbox,)
from speech_translate.ui.custom.spinbox import (SpinboxNumOnly, max_number,
                                                max_number_float, num_check,
                                                number_only,
                                                number_only_float,)
from speech_translate.ui.custom.tooltip import (CreateToolTipOnText, Tooltip,
                                                tk_tooltip, tk_tooltips,)

__all__ = ['AlignmentDialog', 'AudioMeter', 'CB_NAV_KEY_SCRIPT',
           'CategorizedComboBox', 'ComboboxTypeOnCustom', 'ComboboxWithKeyNav',
           'CreateToolTipOnText', 'CustomCheckButton', 'DraggableHtmlLabel',
           'FileImportDialog', 'FileOperationDialog', 'FileProcessDialog',
           'LabelTitleText', 'MBoxText', 'ModResultInputDialog',
           'MultipleChoiceQuestion', 'QueueDialog', 'RefinementDialog',
           'SpinboxNumOnly', 'Tooltip', 'TranslateResultDialog', 'audio',
           'checkbutton', 'combobox', 'dialog', 'download',
           'faster_whisper_download_with_progress_gui', 'label', 'max_number',
           'max_number_float', 'mbox', 'message', 'num_check', 'number_only',
           'number_only_float', 'prompt_with_choices', 'snapshot_download',
           'spinbox', 'tk_tooltip', 'tk_tooltips', 'tooltip',
           'whisper_download_with_progress_gui']

from speech_translate.utils import audio
from speech_translate.utils import custom
from speech_translate.utils import helper
from speech_translate.utils import setting
from speech_translate.utils import tk
from speech_translate.utils import translate
from speech_translate.utils import types
from speech_translate.utils import whisper

from speech_translate.utils.helper import (bind_focus_recursively,
                                           cbtn_invoker, change_file_w_f_call,
                                           change_folder_w_f_call,
                                           choose_color, emoji_img,
                                           filename_only, generate_color,
                                           generate_temp_filename,
                                           get_list_of_dict,
                                           get_opposite_hex_color, get_proxies,
                                           get_similar_in_list,
                                           get_similar_keys,
                                           insert_entry_readonly, kill_thread,
                                           native_notify, no_connection_notify,
                                           open_folder, open_url, popup_menu,
                                           rate_similarity, start_file,
                                           str_separator_to_html, tb_copy_only,
                                           unique_rec_list, up_first_case,
                                           windows_os_only, wrap_result,)
from speech_translate.utils.setting import (SettingJson, default_setting,)
from speech_translate.utils.types import (OriSegmentResult, OriWordResult,
                                          SettingDict, StableTsResultDict,
                                          StableTsSegmentResult,
                                          StableTsWordResult, ToInsert,)

__all__ = ['OriSegmentResult', 'OriWordResult', 'SettingDict', 'SettingJson',
           'StableTsResultDict', 'StableTsSegmentResult', 'StableTsWordResult',
           'ToInsert', 'audio', 'bind_focus_recursively', 'cbtn_invoker',
           'change_file_w_f_call', 'change_folder_w_f_call', 'choose_color',
           'custom', 'default_setting', 'emoji_img', 'filename_only',
           'generate_color', 'generate_temp_filename', 'get_list_of_dict',
           'get_opposite_hex_color', 'get_proxies', 'get_similar_in_list',
           'get_similar_keys', 'helper', 'insert_entry_readonly',
           'kill_thread', 'native_notify', 'no_connection_notify',
           'open_folder', 'open_url', 'popup_menu', 'rate_similarity',
           'setting', 'start_file', 'str_separator_to_html', 'tb_copy_only',
           'tk', 'translate', 'types', 'unique_rec_list', 'up_first_case',
           'whisper', 'windows_os_only', 'wrap_result']

from speech_translate.ui import custom
from speech_translate.ui import frame
from speech_translate.ui import template
from speech_translate.ui import window

__all__ = ['custom', 'frame', 'template', 'window']

from speech_translate import linker
from speech_translate import ui
from speech_translate import utils

from speech_translate.linker import (BridgeClass, bc,)

__all__ = ['BridgeClass', 'bc', 'linker', 'ui', 'utils']