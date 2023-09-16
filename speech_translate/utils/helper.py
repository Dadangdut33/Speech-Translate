import os
import random
import subprocess
import webbrowser
import platform

import tkinter as tk
from datetime import datetime
from tkinter import colorchooser, ttk
from typing import Dict, Union, List
from notifypy import Notify, exceptions
from PIL import Image, ImageDraw, ImageFont, ImageTk
from speech_translate.components.custom.tooltip import tk_tooltip
from speech_translate.custom_logging import logger
from speech_translate._path import app_icon, app_icon_missing
from speech_translate._constants import APP_NAME


def up_first_case(string: str):
    return string[0].upper() + string[1:]


def get_similar_keys(_dict: Dict, key: str):
    return [k for k in _dict.keys() if key.lower() in k.lower()]


def get_proxies(proxy_http: str, proxy_https: str):
    """
    Proxies in setting is saved in a string format separated by \n
    This function will convert it to a dict format and get the proxies randomly
    """
    proxies = {}
    if proxy_http != "":
        http_list = proxy_http.split()
        http_list = [word for word in http_list if any(char.isalpha() for char in word)]
        proxies["http"] = random.choice(http_list)
    if proxy_https != "":
        https_list = proxy_https.split()
        https_list = [word for word in https_list if any(char.isalpha() for char in word)]
        proxies["https"] = random.choice(https_list)
    return proxies


def cbtn_invoker(settingVal: bool, widget: Union[ttk.Checkbutton, ttk.Radiobutton]):
    """
    Checkbutton invoker
    Invoking twice will make it unchecked
    """
    if settingVal:
        widget.invoke()
    else:
        widget.invoke()
        widget.invoke()


def start_file(filename: str):
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


def generate_temp_filename(base_dir):
    """
    Generates a temporary filename with the current date and time.
    """
    return os.path.join(base_dir, datetime.now().strftime("%Y-%m-%d %H_%M_%S_%f")) + ".wav"


def filename_only(filename: str):
    """
    Extracts the name of the file only from a given filename, considering
    the last dot as the separator.

    Parameters
    ----------
    filename (str): The filename, which may contain multiple dots with / as the path separator.

    Returns
    -------
    str: The file name without the dot.
    """
    filename = filename.split("/")[-1]  # Get the last part of the path
    filename = filename.rsplit(".", 1)[0]  # Split the filename at the last dot
    return filename


def chooseColor(theWidget, initialColor, parent):
    color = colorchooser.askcolor(initialcolor=initialColor, title="Choose a color", parent=parent)
    if color[1] is not None:
        theWidget.delete(0, "end")
        theWidget.insert(0, color[1])


def popup_menu(root: Union[tk.Tk, tk.Toplevel], menu: tk.Menu):
    """
    Display popup menu
    """
    try:
        menu.tk_popup(root.winfo_pointerx(), root.winfo_pointery(), 0)
    finally:
        menu.grab_release()


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


def number_only(P):
    return P.isdigit()


def number_only_float(P):
    try:
        float(P)
    except ValueError:
        return False
    return True


def keybind_num_only(event, func):
    v = event.char
    try:
        v = int(v)
        func()
    except ValueError:
        if v != "\x08" and v != "":
            return "break"


def emoji_img(size, text):
    font = ImageFont.truetype("seguiemj.ttf", size=int(round(size * 72 / 96, 0)))
    # pixels = points * 96 / 72 : 96 is windowsDPI
    im = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(im)
    draw.text((size / 2, size / 2), text, embedded_color=True, font=font, anchor="mm")
    return ImageTk.PhotoImage(im)


def num_check(el, min: int, max: int, cb_func=None, converts_to_float=False):
    value = el.get()

    converts_to = float if converts_to_float else int
    if converts_to(value) > max:
        el.set(max)

    if converts_to(value) < min:
        el.set(min)

    if cb_func is not None:
        cb_func()


def max_number(root, el, min: int, max: int, cb_func=None):
    # verify value only after user has finished typing
    root.after(1000, lambda: num_check(el, min, max, cb_func))


def max_number_float(root, el, min: int, max: int, cb_func=None):
    # verify value only after user has finished typing
    root.after(1000, lambda: num_check(el, min, max, cb_func, True))


def bind_focus_recursively(root, root_widget):
    """
    Bind focus on widgets recursively
    """
    widgets = root_widget.winfo_children()

    # now check if there are any children of the children
    for widget in widgets:
        if len(widget.winfo_children()) > 0:
            bind_focus_recursively(root, widget)

        if (
            isinstance(widget, tk.Frame)
            or isinstance(widget, ttk.Frame)
            or isinstance(widget, tk.LabelFrame)
            or isinstance(widget, ttk.LabelFrame)
            or isinstance(widget, tk.Label)
            or isinstance(widget, ttk.Label)
        ):
            # make sure that Button-1 is not already binded
            if "<Button-1>" not in widget.bind():
                widget.bind("<Button-1>", lambda event: root.focus_set())


def windows_os_only(
    widgets: List[
        Union[
            ttk.Checkbutton,
            ttk.Radiobutton,
            ttk.Entry,
            ttk.Combobox,
            ttk.Button,
            ttk.Labelframe,
            tk.LabelFrame,
            ttk.Frame,
            tk.Frame,
            tk.Label,
            ttk.Label,
            tk.Scale,
            ttk.Scale,
        ]
    ]
):
    """
    Disable widgets that are not available on Windows OS

    Args
    ----
        widgets (List[ Union[ ttk.Checkbutton, ttk.Radiobutton, ttk.Entry, ttk.Combobox, ttk.Button, ttk.Labelframe, tk.LabelFrame, ttk.Frame, tk.Frame, ] ]):
            List of widgets to disable
    """
    if platform.system() != "Windows":
        hide = [ttk.LabelFrame, tk.LabelFrame, ttk.Frame, tk.Frame]

        for widget in widgets:
            if widget.winfo_class() in hide:
                assert isinstance(widget, (ttk.LabelFrame, tk.LabelFrame, ttk.Frame, tk.Frame))
                widget.pack_forget()
            else:
                assert isinstance(
                    widget,
                    (ttk.Checkbutton, ttk.Radiobutton, ttk.Entry, ttk.Combobox, ttk.Button, ttk.Label, tk.Scale, ttk.Scale),
                )
                widget.configure(state="disabled")
                tk_tooltip(widget, "This feature is only available on Windows OS.")
