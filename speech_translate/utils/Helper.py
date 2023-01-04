import os
import subprocess
import webbrowser
from notifypy import Notify, exceptions
from speech_translate.Logging import logger

modelSelectDict = {"Tiny (~32x speed)": "tiny", "Base (~16x speed)": "base", "Small (~6x speed)": "small", "Medium (~2x speed)": "medium", "Large (1x speed)": "large"}
modelKeys = list(modelSelectDict.keys())
modelValues = list(modelSelectDict.values())


def upFirstCase(string: str):
    return string[0].upper() + string[1:]


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
