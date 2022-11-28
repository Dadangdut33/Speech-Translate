import os
import subprocess

import webbrowser
from notifypy import Notify, exceptions

from speech_translate.Logging import logger

modelSelectDict = {"Tiny (~32x speed)": "tiny", "Base (~16x speed)": "base", "Small (~6x speed)": "small", "Medium (~2x speed)": "medium", "Large (1x speed)": "large"}
modelKeys = list(modelSelectDict.keys())
modelValues = list(modelSelectDict.values())


def upFirstCase(string):
    return string[0].upper() + string[1:]


def startFile(filename):
    """
    Open a folder or file in the default application.
    """
    try:
        os.startfile(filename)
    except FileNotFoundError:
        logger.exception("Cannot find the file specified.")
    except Exception:
        try:
            subprocess.Popen(["xdg-open", filename])
        except FileNotFoundError:
            logger.exception("Cannot open the file specified.")
        except Exception as e:
            logger.exception("Error: " + str(e))


def OpenUrl(url):
    """
    To open a url in the default browser
    """
    try:
        webbrowser.open_new(url)
    except Exception as e:
        logger.exception(e)
        nativeNotify("Error", "Cannot open the url specified.", "", "Speech Translate")


def nativeNotify(title, message, logo, app_name):
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
