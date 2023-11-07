__all__ = ["default_setting", "SettingJson"]
import json
from os import makedirs, path
from typing import List

from darkdetect import isDark
from notifypy import Notify
from loguru import logger

from speech_translate._version import __setting_version__
from speech_translate.ui.custom.message import mbox
from speech_translate.utils.types import SettingDict

default_setting: SettingDict = {
    "version": __setting_version__,
    "checkUpdateOnStart": True,
    "first_open": True,
    # ------------------ #
    # App settings
    "transcribe": True,
    "translate": True,
    "input": "mic",  # mic, speaker
    "model": "small",
    "verbose": False,
    "separate_with": "\\n",
    "mic": "",
    "speaker": "",
    "hostAPI": "",
    "theme": "sun-valley-dark" if isDark() else "sun-valley-light",
    "supress_hidden_to_tray": False,
    "supress_device_warning": False,
    "mw_size": "1000x500",
    "sw_size": "1000x620",
    "dir_log": "auto",
    "dir_model": "auto",
    "file_slice_start": "",  # empty will be read as None
    "file_slice_end": "",  # empty will be read as None
    "parse_arabic": True,
    # ------------------ #
    # logging
    "keep_log": False,
    "log_level": "DEBUG",  # INFO DEBUG WARNING ERROR
    "auto_scroll_log": True,
    "auto_refresh_log": True,
    "ignore_stdout": ["Predicting silences(s) with VAD...", "Predicted silences(s) with VAD"],
    "debug_realtime_record": False,
    "debug_translate": False,
    # ------------------ #
    # Tl Settings
    "sourceLang": "English",
    "targetLang": "Indonesian",
    "tl_engine": "Google Translate",
    "https_proxy": "",
    "https_proxy_enable": False,
    "http_proxy": "",
    "http_proxy_enable": False,
    "libre_api_key": "",
    "libre_host": "",
    "libre_port": "",
    "libre_https": True,
    # ------------------ #
    # Record settings
    "debug_recorded_audio": False,
    # temp
    "use_temp": False,
    "max_temp": 200,
    "keep_temp": False,
    # mic - device option
    "sample_rate_mic": 16000,
    "channels_mic": "Mono",  # Mono, Stereo, custom -> "1", "2", ...
    "chunk_size_mic": 1024,
    "auto_sample_rate_mic": False,
    "auto_channels_mic": False,
    # mic - record option
    "threshold_enable_mic": True,
    "threshold_auto_mic": True,
    "threshold_auto_mode_mic": 3,
    "threshold_db_mic": -20.0,
    "auto_break_buffer_mic": True,
    "max_buffer_mic": 10,
    "max_sentences_mic": 5,
    # speaker - device option
    "sample_rate_speaker": 44100,
    "channels_speaker": "Stereo",
    "chunk_size_speaker": 1024,
    "auto_sample_rate_speaker": True,
    "auto_channels_speaker": True,
    # speaker - record option
    "threshold_enable_speaker": True,
    "threshold_auto_speaker": True,
    "threshold_auto_mode_speaker": 3,
    "threshold_db_speaker": -20.0,
    "auto_break_buffer_speaker": False,
    "max_buffer_speaker": 10,
    "max_sentences_speaker": 5,
    # Transcribe settings
    "dir_export": "auto",
    "auto_open_dir_export": True,
    "auto_open_dir_refinement": True,
    "auto_open_dir_alignment": True,
    "auto_open_dir_translate": True,
    # {file} {task} {task-short} {lang-source} {lang-target} {model} {engine}
    "export_format": "%Y-%m-%d %H_%M {file}_{task}",
    # txt csv json srt ass vtt tsv
    "export_to": ["txt", "srt", "json"],
    "segment_level": True,  # 1 of this must be true
    "word_level": True,  # 1 of this must be true
    "visualize_suppression": False,
    "use_faster_whisper": True,
    "transcribe_rate": 300,
    "decoding_preset": "beam search",  # greedy, beam search, custom
    "temperature": "0.0, 0.2, 0.4, 0.6, 0.8, 1.0",  # 0.0 - 1.0
    "best_of": 5,
    "beam_size": 5,
    "compression_ratio_threshold": 2.4,
    "logprob_threshold": -1.0,
    "no_speech_threshold": 0.6,
    "suppress_tokens": "-1",
    "initial_prompt": "",
    "condition_on_previous_text": True,
    "whisper_args": "",
    # ------------------ #
    # Textboxes
    "colorize_per_segment": True,
    "colorize_per_word": False,
    "gradient_low_conf": "#FF0000",
    "gradient_high_conf": "#00FF00",
    # mw tc
    "tb_mw_tc_limit_max": False,
    "tb_mw_tc_limit_max_per_line": False,
    "tb_mw_tc_max": 300,
    "tb_mw_tc_max_per_line": 30,
    "tb_mw_tc_font": "TKDefaultFont",
    "tb_mw_tc_font_bold": False,
    "tb_mw_tc_font_size": 10,
    "tb_mw_tc_use_conf_color": True,
    # mw tl
    "tb_mw_tl_limit_max": False,
    "tb_mw_tl_limit_max_per_line": False,
    "tb_mw_tl_max": 300,
    "tb_mw_tl_max_per_line": 30,
    "tb_mw_tl_font": "TKDefaultFont",
    "tb_mw_tl_font_bold": False,
    "tb_mw_tl_font_size": 10,
    "tb_mw_tl_use_conf_color": True,
    # Tc sub
    "ex_tc_geometry": "800x200",
    "ex_tc_always_on_top": 1,
    "ex_tc_click_through": 0,
    "ex_tc_no_title_bar": 1,
    "ex_tc_no_tooltip": 0,
    "tb_ex_tc_limit_max": False,
    "tb_ex_tc_limit_max_per_line": False,
    "tb_ex_tc_max": 120,
    "tb_ex_tc_max_per_line": 30,
    "tb_ex_tc_font": "Arial",
    "tb_ex_tc_font_bold": True,
    "tb_ex_tc_font_size": 13,
    "tb_ex_tc_font_color": "#FFFFFF",
    "tb_ex_tc_bg_color": "#000000",
    "tb_ex_tc_use_conf_color": True,
    # Tl sub
    "ex_tl_geometry": "800x200",
    "ex_tl_always_on_top": 1,
    "ex_tl_click_through": 0,
    "ex_tl_no_title_bar": 1,
    "ex_tl_no_tooltip": 0,
    "tb_ex_tl_limit_max": False,
    "tb_ex_tl_limit_max_per_line": False,
    "tb_ex_tl_max": 120,
    "tb_ex_tl_max_per_line": 30,
    "tb_ex_tl_font": "Arial",
    "tb_ex_tl_font_bold": True,
    "tb_ex_tl_font_size": 13,
    "tb_ex_tl_font_color": "#FFFFFF",
    "tb_ex_tl_bg_color": "#000000",
    "tb_ex_tl_use_conf_color": True
}


class SettingJson:
    """
    Class to handle setting.json
    """
    def __init__(self, setting_path: str, setting_dir: str, checkdirs: List[str]):
        self.cache: SettingDict = {}  # type: ignore
        self.setting_path = setting_path
        self.dir = setting_dir
        self.createDirectoryIfNotExist(self.dir)  # setting dir
        for checkdir in checkdirs:
            self.createDirectoryIfNotExist(checkdir)
        self.createDefaultSettingIfNotExist()  # setting file

        # Load setting
        success, msg, data = self.loadSetting()
        if success:
            self.cache = data
            # verify loaded setting
            success, msg, data = self.verifyLoadedSetting(data)
            if not success:
                self.cache = default_setting
                notification = Notify()
                notification.application_name = "Speech Translate"
                notification.title = "Error: Verifying setting file"
                notification.message = "Setting reverted to default. Details: " + msg
                notification.send()
                logger.warning("Error verifying setting file: " + msg)

            # verify setting version
            if self.cache["version"] != __setting_version__:
                # save old one as backup
                self.save_old_setting(self.cache)
                self.cache = default_setting  # load default
                self.cache["first_open"] = False  # keep first_open to false because it's not first open
                self.save(self.cache)  # save
                notification = Notify()
                notification.application_name = "Speech Translate"
                notification.title = "Setting file is outdated"
                notification.message = "Setting file is outdated. Setting has been reverted to default setting."
                notification.send()
                logger.warning(
                    "Setting file is outdated. Setting has been reverted to default setting. "
                    "You can find your old setting in the user folder."
                )

            logger.info("Setting loaded")
        else:
            self.cache = default_setting
            logger.error("Error loading setting file: " + msg)
            mbox("Error", "Error: Loading setting file. " + self.setting_path + "\nReason: " + msg, 2)

    def createDirectoryIfNotExist(self, dir: str):
        """
        Create directory if it doesn't exist
        """
        try:
            if not path.exists(dir):
                makedirs(dir)
        except Exception as e:
            mbox("Error", "Error: Creating directory. " + dir + "\nReason: " + str(e), 2)

    def createDefaultSettingIfNotExist(self):
        """
        Create default json file if it doesn't exist
        """
        setting_path = self.setting_path
        try:
            if not path.exists(setting_path):
                with open(setting_path, "w", encoding="utf-8") as f:
                    json.dump(default_setting, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.exception(e)
            mbox("Error", "Error: Creating default setting file. " + setting_path + "\nReason: " + str(e), 2)

    def save(self, data: SettingDict):
        """
        Save json file
        """
        success: bool = False
        msg: str = ""
        try:
            with open(self.setting_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            success = True
            self.cache = data
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg

    def save_cache(self):
        """
        Save but from cache
        """
        return self.save(self.cache)

    def save_old_setting(self, data: SettingDict):
        """
        Save json file
        """
        success: bool = False
        msg: str = ""
        try:
            with open(
                self.setting_path.replace("setting.json", f"setting_old_{data['version']}.json"),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg

    def save_key(self, key: str, value):
        """
        Save only a part of the setting
        """
        if key not in self.cache:
            logger.error("Error saving setting: " + key + " not in cache")
            return
        if self.cache[key] == value:  # if same value
            return

        self.cache[key] = value
        success, msg = self.save(self.cache)

        if not success:
            notification = Notify()
            notification.application_name = "Speech Translate"
            notification.title = "Error: Saving setting file"
            notification.message = "Reason: " + msg
            notification.send()
            logger.error("Error saving setting file: " + msg)

    def loadSetting(self):
        """
        Load json file
        """
        success: bool = False
        msg: str = ""
        data: SettingDict = {}  # type: ignore
        try:
            with open(self.setting_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg, data

    def verifyLoadedSetting(self, data: SettingDict):
        """
        Verify loaded setting
        """
        success: bool = False
        msg: str = ""
        try:
            # check each key
            for key in default_setting:
                if key not in data:
                    data[key] = default_setting[key]

            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg, data

    def getSetting(self):
        """
        Get setting value
        """
        return self.cache
