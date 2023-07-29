__all__ = ["default_setting", "SettingJson"]
import json
import os
import darkdetect
from typing import List

from notifypy import Notify

from speech_translate.components.custom.message import mbox
from speech_translate.custom_logging import logger
from speech_translate._version import __setting_version__

default_setting = {
    "version": __setting_version__,
    "checkUpdateOnStart": True,
    # ------------------ #
    # App settings
    "mode": "Transcribe",
    "model": "tiny",
    "verbose": False,
    "hide_console_window_on_start": False,
    "separate_with": "\\n",
    "mic": "",
    "speaker": "",
    "theme": "sv-dark" if darkdetect.isDark() else "sv-light",
    "dir_export": "auto",
    "auto_open_dir_export": True,
    "supress_hidden_to_tray": False,
    "supress_device_warning": False,
    "mw_size": "1200x400",
    "sw_size": "1000x580",
    # ------------------ #
    # logging
    "keep_log": False,
    "log_level": "DEBUG",  # INFO DEBUG WARNING ERROR
    "auto_scroll_log": True,
    "auto_refresh_log": True,
    "debug_realtime_record": False,
    "debug_translate": False,
    # ------------------ #
    # Tl Settings
    "sourceLang": "Auto Detect",
    "targetLang": "Indonesian",
    "tl_engine": "Google",
    "libre_api_key": "",
    "libre_host": "translate.argosopentech.com",
    "libre_port": "",
    "libre_https": True,
    # ------------------ #
    # Record settings
    "mic_maxBuffer": 10,
    "speaker_maxBuffer": 10,
    "mic_energy_threshold": 5000,
    "speaker_energy_threshold": 5000,
    "enable_threshold": False,
    "debug_energy": False,
    "transcribe_rate": 300,
    "sample_rate": 16000,
    "chunk_size": 1024,
    "max_sentences": 5,
    "max_temp": 200,
    "auto_sample_rate": False,
    "auto_channels_amount": False,
    "keep_temp": False,
    # Whisper settings
    "whisper_extra_args": "",
    "temperature": "0.0, 0.2, 0.4, 0.6, 0.8, 1.0",
    "compression_ratio_threshold": 2.4,
    "logprob_threshold": -1.0,
    "no_speech_threshold": 0.6,
    "condition_on_previous_text": True,
    "initial_prompt": "",
    # ------------------ #
    # Textboxes
    "tb_mw_tc_max": 0,
    "tb_mw_tc_font": "TKDefaultFont",
    "tb_mw_tc_font_bold": False,
    "tb_mw_tc_font_size": 10,
    "tb_mw_tl_max": 0,
    "tb_mw_tl_font": "TKDefaultFont",
    "tb_mw_tl_font_bold": False,
    "tb_mw_tl_font_size": 10,
    # Tc sub
    "ex_tc_bg": "#00ff00",
    "ex_tc_always_on_top": 1,
    "ex_tc_click_through": 1,
    "ex_tc_no_title_bar": 1,
    "ex_tc_no_tooltip": 1,
    "tb_ex_tc_max": 0,
    "tb_ex_tc_font": "Helvetica",
    "tb_ex_tc_font_bold": True,
    "tb_ex_tc_font_size": 12,
    "tb_ex_tc_font_color": "#FFFFFF",
    "tb_ex_tc_bg_color": "#000000",
    # Tl sub
    "ex_tl_bg": "#00ff00",
    "ex_tl_always_on_top": 1,
    "ex_tl_click_through": 1,
    "ex_tl_no_title_bar": 1,
    "ex_tl_no_tooltip": 1,
    "tb_ex_tl_max": 0,
    "tb_ex_tl_font": "Helvetica",
    "tb_ex_tl_font_bold": True,
    "tb_ex_tl_font_size": 12,
    "tb_ex_tl_font_color": "#FFFFFF",
    "tb_ex_tl_bg_color": "#000000",
}


class SettingJson:
    """
    Class to handle setting.json
    """

    def __init__(self, settingPath: str, settingDir: str, checkdirs: List[str]):
        self.cache = {}
        self.path = settingPath
        self.dir = settingDir
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
                self.saveOldSetting(self.cache)
                self.cache = default_setting  # load default
                self.saveSetting(self.cache)  # save
                # notify
                notification = Notify()
                notification.application_name = "Speech Translate"
                notification.title = "Setting file is outdated"
                notification.message = "Setting file is outdated. Setting has been reverted to default setting."
                notification.send()
                logger.warning("Setting file is outdated. Setting has been reverted to default setting. You can find your old setting in the user folder.")
        else:
            self.cache = default_setting
            logger.error("Error loading setting file: " + msg)
            mbox("Error", "Error: Loading setting file. " + self.path + "\nReason: " + msg, 2)

    def createDirectoryIfNotExist(self, path: str):
        """
        Create directory if it doesn't exist
        """
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except Exception as e:
            mbox("Error", "Error: Creating directory. " + path + "\nReason: " + str(e), 2)

    def createDefaultSettingIfNotExist(self):
        """
        Create default json file if it doesn't exist
        """
        path = self.path
        try:
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(default_setting, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.exception(e)
            mbox("Error", "Error: Creating default setting file. " + path + "\nReason: " + str(e), 2)

    def saveSetting(self, data: dict):
        """
        Save json file
        """
        success: bool = False
        msg: str = ""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            success = True
            self.cache = data
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg

    def saveOldSetting(self, data: dict):
        """
        Save json file
        """
        success: bool = False
        msg: str = ""
        try:
            with open(self.path.replace("setting.json", f"setting_old_{data['version']}.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg

    def savePartialSetting(self, key: str, value):
        """
        Save only a part of the setting
        """
        self.cache[key] = value
        success, msg = self.saveSetting(self.cache)

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
        data: dict = {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg, data

    def verifyLoadedSetting(self, data: dict):
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
