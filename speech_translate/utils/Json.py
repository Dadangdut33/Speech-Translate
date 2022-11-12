__all__ = ["default_setting", "SettingJsonHandler"]
import json
import os

from components.MBox import Mbox  # uses message box for error because this is important
from notifypy import Notify


default_setting = {
    "mode": "Transcribe",
    "model": "tiny",
    "sourceLang": "English",
    "targetLang": "Indonesian",
    "verbose": False,
    "keep_audio": False,
    "max_temp": 100,
    "cutOff": 5,
    "separate_with": "\n",
    "tl_engine": "Google",
    "libre_api_key": "",
    "libre_host": "libretranslate.de",
    "libre_port": "",
    "libre_https": True,
    "textbox": {
        "mw_tc": {
            "max": 1000,
        },
        "mw_tl": {
            "max": 1000,
        },
        "detached_tc": {
            "max": 1000,
        },
        "detached_tl": {
            "max": 1000,
        },
    },
}


class SettingJsonHandler:
    """
    Class to handle setting.json
    """

    def __init__(self, settingPath: str, settingDir: str, tempDir: str):
        self.settingCache = {}
        self.settingPath = settingPath
        self.settingDir = settingDir
        self.createDirectoryIfNotExist(self.settingDir)
        self.createDefaultSettingIfNotExist(self.settingPath, default_setting)
        self.createDirectoryIfNotExist(tempDir)

        # Load setting
        success, msg, data = self.loadSetting()
        if success:
            self.settingCache = data
        else:
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

    def getSetting(self):
        """
        Get setting value
        """
        return self.settingCache
