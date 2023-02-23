import os
import subprocess
import webbrowser
from typing import Dict
from notifypy import Notify, exceptions
from speech_translate.Logging import logger

def upFirstCase(string: str):
    return string[0].upper() + string[1:]


def get_similar_keys(_dict: Dict, key: str):
    return [k for k in _dict.keys() if key.lower() in k.lower()]


def startFile(filename: str):
    """
    Open a folder or file in the default application.
    """
    try:
        os.startfile(filename)
    except FileNotFoundError:
        logger.exception("Cannot find the file specified.")
        nativeNotify("Error", "Cannot find the file specified.", "", "Speech Translate")
    except Exception:
        try:
            subprocess.Popen(["xdg-open", filename])
        except FileNotFoundError:
            logger.exception("Cannot open the file specified.")
            nativeNotify("Error", "Cannot find the file specified.", "", "Speech Translate")
        except Exception as e:
            logger.exception("Error: " + str(e))
            nativeNotify("Error", f"Uncaught error {str(e)}", "", "Speech Translate")


def OpenUrl(url: str):
    """
    To open a url in the default browser
    """
    try:
        webbrowser.open_new(url)
    except Exception as e:
        logger.exception(e)
        nativeNotify("Error", "Cannot open the url specified.", "", "Speech Translate")


def nativeNotify(title: str, message: str, logo: str, app_name: str):
    """
    Native notification
    """
    notification = Notify()
    notification.application_name = app_name
    notification.title = title
    notification.message = message
    try:
        notification.icon = logo
    except exceptions:
        pass

    notification.send()



def getFileNameOnlyFromPath(path: str):
    return path.split("/")[-1]


def tb_copy_only(event):
    key = event.keysym

    # Allow
    allowedEventState = [4, 8, 12]
    if key.lower() in ["left", "right"]:  # Arrow left right
        return
    if event.state in allowedEventState and key.lower() == "a":  # Ctrl + a
        return
    if event.state in allowedEventState and key.lower() == "c":  # Ctrl + c
        return

    # If not allowed
    return "break"
