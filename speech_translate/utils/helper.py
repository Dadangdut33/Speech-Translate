import os
import subprocess
import webbrowser

from tkinter import colorchooser, ttk
from typing import Dict
from notifypy import Notify, exceptions
from speech_translate.custom_logging import logger
from speech_translate._path import app_icon, app_icon_missing
from speech_translate._contants import APP_NAME


def upFirstCase(string: str):
    return string[0].upper() + string[1:]


def get_similar_keys(_dict: Dict, key: str):
    return [k for k in _dict.keys() if key.lower() in k.lower()]


def cbtnInvoker(settingVal: bool, widget: ttk.Checkbutton):
    if settingVal:
        widget.invoke()
    else:
        widget.invoke()
        widget.invoke()


def startFile(filename: str):
    """
    Open a folder or file in the default application.
    """
    try:
        os.startfile(filename)
    except FileNotFoundError:
        logger.exception("Cannot find the file specified.")
        nativeNotify("Error", "Cannot find the file specified.")
    except Exception:
        try:
            subprocess.Popen(["xdg-open", filename])
        except FileNotFoundError:
            logger.exception("Cannot open the file specified.")
            nativeNotify("Error", "Cannot find the file specified.")
        except Exception as e:
            logger.exception("Error: " + str(e))
            nativeNotify("Error", f"Uncaught error {str(e)}")


def OpenUrl(url: str):
    """
    To open a url in the default browser
    """
    try:
        webbrowser.open_new(url)
    except Exception as e:
        logger.exception(e)
        nativeNotify("Error", "Cannot open the url specified.")


def nativeNotify(title: str, message: str):
    """
    Native notification
    """
    notification = Notify()
    notification.application_name = APP_NAME
    notification.title = title
    notification.message = message
    if not app_icon_missing:
        try:
            notification.icon = app_icon
        except exceptions:
            pass

    notification.send()


def no_connection_notify(
    customTitle: str = "No Internet Connection",
    customMessage: str = "Translation for engine other than Whisper or your local LibreTranslate Deployment (If you have one) will not work until you reconnect to the internet.",
):
    """
    Notify user that they are not connected to the internet
    """
    nativeNotify(customTitle, customMessage)


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

def chooseColor(theWidget, initialColor, parent):
    color = colorchooser.askcolor(initialcolor=initialColor, title="Choose a color", parent=parent)
    if color[1] is not None:
        theWidget.delete(0, "end")
        theWidget.insert(0, color[1])