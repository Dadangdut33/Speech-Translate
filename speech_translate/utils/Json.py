import json
import os

from components.MBox import Mbox


default_setting = {
    "source_language": "en",
    "target_language": "id",
}


class JsonHandler:
    """
    Class to handle json files
    """

    def __init__(self, settingPath: str, settingDir: str):
        self.settingCache = {}
        self.settingPath = settingPath
        self.settingDir = settingDir
        self.createDirectoryIfNotExist(self.settingDir)
        self.createDefaultSettingIfNotExist(self.settingPath, default_setting)

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
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg

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
