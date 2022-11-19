__all__ = ["default_setting", "SettingJsonHandler"]
import json
import os
import sys

from components.MBox import Mbox  # uses message box for error because this is important
from notifypy import Notify

sys.path.append("..")
from Logging import logger
from _version import __setting_version__

default_setting = {
    "version": __setting_version__,
    "mode": "Transcribe",
    "model": "tiny",
    "sourceLang": "English",
    "targetLang": "Indonesian",
    "verbose": False,
    "keep_audio": False,
    "keep_log": False,
    "max_temp": 100,
    "cutOff": {"mic": 5, "speaker": 5},
    "separate_with": "\n",
    "tl_engine": "Google",
    "libre_api_key": "",
    "libre_host": "libretranslate.de",
    "libre_port": "",
    "libre_https": True,
    "mic": "",
    "speaker": "",
    "textbox": {
        "mw_tc": {
            "max": 1000,
            "font": "TKDefaultFont",
            "font_size": 10,
            "font_color": "#000000",
            "bg_color": "#FFFFFF",
        },
        "mw_tl": {
            "max": 1000,
            "font": "TKDefaultFont",
            "font_size": 10,
            "font_color": "#000000",
            "bg_color": "#FFFFFF",
        },
        "detached_tc": {
            "max": 1000,
            "font": "TKDefaultFont",
            "font_size": 10,
            "font_color": "#000000",
            "bg_color": "#FFFFFF",
            "opacity": 0.8,
        },
        "detached_tl": {
            "max": 1000,
            "font": "TKDefaultFont",
            "font_size": 10,
            "font_color": "#000000",
            "bg_color": "#FFFFFF",
            "opacity": 0.8,
        },
    },
}


class SettingJsonHandler:
    """
    Class to handle setting.json
    """

    def __init__(self, settingPath: str, settingDir: str, tempDir: str, logDir: str):
        self.settingCache = {}
        self.settingPath = settingPath
        self.settingDir = settingDir
        self.createDirectoryIfNotExist(self.settingDir)  # setting dir
        self.createDefaultSettingIfNotExist(self.settingPath, default_setting)  # setting file
        self.createDirectoryIfNotExist(tempDir)  # temp dir
        self.createDirectoryIfNotExist(logDir)  # log dir

        # Load setting
        success, msg, data = self.loadSetting()
        if success:
            self.settingCache = data
            # verify loaded setting
            success, msg, data = self.verifyLoadedSetting(data)
            if not success:
                self.settingCache = default_setting
                notification = Notify()
                notification.application_name = "Speech Translate"
                notification.title = "Error: Verifying setting file"
                notification.message = "Setting reverted to default. Details: " + msg
                notification.send()
                logger.warning("Error verifying setting file: " + msg)

            # verify setting version
            if self.settingCache["version"] != __setting_version__:
                self.settingCache = default_setting  # load default
                self.saveSetting(self.settingCache)  # save
                # notify
                notification = Notify()
                notification.application_name = "Speech Translate"
                notification.title = "Setting file is outdated"
                notification.message = "Setting file is outdated. Setting has been reverted to default setting."
                notification.send()
                logger.warning("Setting file is outdated. Setting has been reverted to default setting.")
        else:
            self.settingCache = default_setting
            logger.error("Error loading setting file: " + msg)
            Mbox("Error", "Error: Loading setting file. " + self.settingPath + "\nReason: " + msg, 2)

    def createDirectoryIfNotExist(self, path: str):
        """
        Create directory if it doesn't exist
        """
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except Exception as e:
            Mbox("Error", "Error: Creating directory. " + path + "\nReason: " + str(e), 2)

    def createDefaultSettingIfNotExist(self, path: str, default: dict):
        """
        Create default json file if it doesn't exist
        """
        try:
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(default, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.exception("Error creating default setting file: " + str(e))
            Mbox("Error", "Error: Creating default setting file. " + path + "\nReason: " + str(e), 2)

    def saveSetting(self, data: dict):
        """
        Save json file
        """
        success: bool = False
        msg: str = ""
        try:
            with open(self.settingPath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            success = True
            self.settingCache = data
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg

    def savePartialSetting(self, key: str, value):
        """
        Save only a part of the setting
        """
        self.settingCache[key] = value
        success, msg = self.saveSetting(self.settingCache)

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
            with open(self.settingPath, "r", encoding="utf-8") as f:
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
        return self.settingCache
