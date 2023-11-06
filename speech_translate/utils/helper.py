import html
import subprocess
import textwrap
import tkinter as tk
import ctypes
from collections import OrderedDict
from datetime import datetime
from os import path, startfile
from platform import system
from random import choice
from subprocess import Popen
from tkinter import colorchooser, ttk
from typing import Dict, List, Union
from webbrowser import open_new
from difflib import SequenceMatcher
from threading import Thread

from stable_whisper import WhisperResult
from loguru import logger
from notifypy import Notify, exceptions
from PIL import Image, ImageDraw, ImageFont, ImageTk

from speech_translate._constants import APP_NAME
from speech_translate._path import app_icon, app_icon_missing, ffmpeg_ps_script
from speech_translate.ui.custom.tooltip import tk_tooltip
from speech_translate.utils.types import ToInsert


def kill_thread(thread: Thread) -> bool:
    ''' Attempt to kill thread, credits: https://github.com/JingheLee/KillThread
    
    Parameters
    ----------
    thread : Thread
        Thread instance object.

    Returns
    -------
    bool
        True or False
    '''
    try:
        if isinstance(thread, Thread):
            return ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), ctypes.py_object(SystemExit)) == 1
        else:
            return False
    except Exception as e:
        logger.exception(e)
        return False


def up_first_case(string: str):
    return string[0].upper() + string[1:]


def get_list_of_dict(list_of_dict: List[Dict], key: str, value):
    return next((item for item in list_of_dict if item[key] == value), None)


def get_similar_keys(_dict: Dict, key: str):
    return [k for k in _dict.keys() if key.lower() in k.lower()]


def unique_rec_list(list_of_data: List):
    # check first, if the list is empty
    if len(list_of_data) == 0:
        return list_of_data

    if isinstance(list_of_data[0], WhisperResult):
        seen = set()
        unique_lists = []
        for obj in list_of_data:
            assert isinstance(obj, WhisperResult)
            if obj.text not in seen:
                unique_lists.append(obj)
                seen.add(obj.text)
    else:
        # Convert the list to a set to get unique values then convert them back to a list
        unique_lists = list(OrderedDict.fromkeys(list_of_data))

    return unique_lists


def generate_color(accuracy, low_color, high_color):
    low_color = low_color[1:]  # Remove the # from the hexadecimal color
    high_color = high_color[1:]  # Remove the # from the hexadecimal color
    # Map accuracy to a custom gradient color between low_color and high_color
    r_low, g_low, b_low = int(low_color[0:2], 16), int(low_color[2:4], 16), int(low_color[4:6], 16)
    r_high, g_high, b_high = int(high_color[0:2], 16), int(high_color[2:4], 16), int(high_color[4:6], 16)

    r = int(r_low + (r_high - r_low) * accuracy)
    g = int(g_low + (g_high - g_low) * accuracy)
    b = int(b_low + (b_high - b_low) * accuracy)

    color = f"#{r:02X}{g:02X}{b:02X}"  # Convert RGB to a hexadecimal color

    return color


def separator_to_html(separator: str):
    # Define the mapping for escape sequences.
    html_equivalents = {
        '\t': '&nbsp;&nbsp;&nbsp;&nbsp;',  # Replace tabs with four non-breaking spaces.
        '\n': '<br>',  # Replace newlines with <br> elements.
        ' ': '&nbsp;',  # Replace regular spaces with non-breaking spaces.
    }
    # render it as safe html
    separator = html.escape(separator)

    # Iterate through the text and apply replacements.
    for char, html_equiv in html_equivalents.items():
        separator = separator.replace(char, html_equiv)

    return separator


def html_to_separator(separator: str):
    # Define the mapping for escape sequences.
    html_equivalents = {
        '&nbsp;&nbsp;&nbsp;&nbsp;': '\t',  # Replace tabs with four non-breaking spaces.
        '<br>': '\n',  # Replace newlines with <br> elements.
        '<br/>': '\n',  # Replace newlines with <br> elements.
        '<br />': '\n',  # Replace newlines with <br> elements.
        '&nbsp;': ' ',  # Replace regular spaces with non-breaking spaces.
    }

    # Iterate through the text and apply replacements.
    for char, html_equiv in html_equivalents.items():
        separator = separator.replace(char, html_equiv)

    return separator


def get_bg_color(window: tk.Tk):
    """
    Get the background color of the window
    """
    bg = window.cget("bg")
    if bg == "SystemButtonFace":
        bg_rgb = window.winfo_rgb("SystemButtonFace")
        background_color = "#{:02X}{:02X}{:02X}".format(bg_rgb[0] // 256, bg_rgb[1] // 256, bg_rgb[2] // 256)
    else:
        background_color = bg

    return background_color


def wrap_result(res: List[ToInsert], max_line_length: int):
    """
    Wrap the result text to a certain length, each sentences should already have its separator in it

    Parameters
    ----------
    res : List[ToInsert]
        List of results to wrap
    max_line_length : int
        Maximum line length

    Returns
    -------
    _type_
        _description_
    """
    wrapped_res: List[ToInsert] = []
    for sentence in res:
        text = sentence['text']
        color = sentence['color']

        # Use textwrap.wrap to wrap the text
        wrapped_text = textwrap.wrap(text, width=max_line_length, break_long_words=False)

        # Create a list of dictionaries with wrapped text and the same color
        wrapped_res.extend([{'text': line, 'color': color, 'is_last': False} for line in wrapped_text])

        if len(wrapped_res) > 0:
            # mark last part of each sentence
            wrapped_res[-1]['is_last'] = True

    return wrapped_res


def get_proxies(proxy_http: str, proxy_https: str):
    """
    Proxies in setting is saved in a string format separated by \n
    This function will convert it to a dict format and get the proxies randomly
    """
    proxies = {}
    if proxy_http != "":
        http_list = proxy_http.split()
        http_list = [word for word in http_list if any(char.isalpha() for char in word)]
        proxies["http"] = choice(http_list)
    if proxy_https != "":
        https_list = proxy_https.split()
        https_list = [word for word in https_list if any(char.isalpha() for char in word)]
        proxies["https"] = choice(https_list)
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


def open_folder(filename: str):
    """
    Open folder of a give filename path

    Parameters
    ----------
    filename : str
        The filename
    """
    if path.exists(filename):
        if path.isdir(filename):
            start_file(filename)
        else:
            start_file(path.dirname(filename))
    else:
        logger.exception("Cannot find the file specified.")
        native_notify("Error", "Cannot find the file specified.")


def start_file(filename: str):
    """
    Open a folder or file in the default application.
    """
    try:
        if system() == 'Darwin':  # macOS
            subprocess.call(('open', filename))
        elif system() == 'Windows':  # Windows
            startfile(filename)
        else:  # linux variants
            subprocess.call(('xdg-open', filename))
    except FileNotFoundError:
        logger.exception("Cannot find the file specified.")
        native_notify("Error", "Cannot find the file specified.")
    except Exception as e:
        logger.exception("Error: " + str(e))
        native_notify("Error", f"Uncaught error {str(e)}")


def check_ffmpeg_in_path():
    """
    Check if ffmpeg is in the path
    """
    success = True
    msg = ""
    try:
        Popen(["ffmpeg", "-version"])
        msg = "ffmpeg is in the path."
    except FileNotFoundError:
        success = False
        msg = "ffmpeg is not in the path."
    except Exception as e:
        success = False
        msg = str(e)
    finally:
        return success, msg


def install_ffmpeg_windows():
    """
    Install ffmpeg on windows
    """
    success = True
    msg = ""
    # first check if the script is in the path
    if not path.exists(ffmpeg_ps_script):
        logger.debug("ffmpeg_ps_script not found. Creating it...")
        # create it directly
        with open(ffmpeg_ps_script, "w") as f:
            f.write(
                r"""
param (
    [switch]$webdl
)

$isAdministrator = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$arguments = [System.Environment]::GetCommandLineArgs()

# MUST BE RUN AS ADMINISTRATOR, but when run from a webdl, it will not be forced
if (-NOT $isAdministrator -AND -NOT $webdl)
{  
  $arguments = "& '" +$myinvocation.mycommand.definition + "'"
  Start-Process powershell -Verb runAs -ArgumentList $arguments
  Break
}

if (-NOT $isAdministrator)
{
  Write-Host "WARNING: This script must be run as administrator to correctly add ffmpeg to the system path."
}

# modified a little from https://adamtheautomator.com/install-ffmpeg/
New-Item -Type Directory -Path C:\ffmpeg 
Set-Location C:\ffmpeg
curl.exe -L 'https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip' -o 'ffmpeg.zip'

# Expand the Zip
Expand-Archive .\ffmpeg.zip -Force -Verbose

# Move the executable (*.exe) files to the top folder
Get-ChildItem -Recurse -Path .\ffmpeg -Filter *.exe |
ForEach-Object {
    $source = $_.FullName
    $destination = Join-Path -Path . -ChildPath $_.Name
    Move-Item -Path $source -Destination $destination -Force -Verbose
}

# # Clean up
Write-Host "Cleaning up..."
Remove-Item .\ffmpeg\ -Recurse
Remove-Item .\ffmpeg.zip

# List the directory contents
Get-ChildItem

# Prepend the FFmpeg folder path to the system path variable
Write-Host "Adding ffmpeg to the system path..."
[System.Environment]::SetEnvironmentVariable(
    "PATH",
    "C:\ffmpeg\;$([System.Environment]::GetEnvironmentVariable('PATH','MACHINE'))",
    "Machine"
)
Write-Host "ffmpeg has been added to the system path."

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")

Write-Host "check it by running ffmpeg -version"    
            """
            )
    logger.debug("Running ps script...")
    # run the script
    p = Popen(
        [
            "powershell", "-ExecutionPolicy", "-noprofile", "-c",
            rf"""Start-Process -Verb RunAs -Wait powershell.exe -Args "-noprofile -c Set-Location \`"$PWD\`"; & {ffmpeg_ps_script}"
            """
        ]
    )
    status = p.wait()

    if status != 0:
        success = False
        msg = "Error installing ffmpeg. Please install it manually."
    else:
        success = True
        msg = "ffmpeg installed successfully."
    return success, msg


def install_ffmpeg_linux():
    """
    Install ffmpeg on linux
    """
    p = Popen(["sudo", "apt", "install", "ffmpeg"])
    status = p.wait()
    if status != 0:
        success = False
        msg = "Error installing ffmpeg. Please install it manually."
    else:
        success = True
        msg = "ffmpeg installed successfully."

    return success, msg


def install_ffmpeg_macos():
    """
    Install ffmpeg on macos
    """
    p = Popen(["brew", "install", "ffmpeg"])
    status = p.wait()
    if status != 0:
        success = False
        msg = "Error installing ffmpeg. Please install it manually."
    else:
        success = True
        msg = "ffmpeg installed successfully."

    return success, msg


def install_ffmpeg():
    """
    Install ffmpeg on all platforms
    """
    if system() == "Windows":
        return install_ffmpeg_windows()
    elif system() == "Linux" or system() == "Linux2":
        return install_ffmpeg_linux()
    elif system() == "Darwin":
        return install_ffmpeg_macos()
    else:
        return False, "Unknown OS."


def OpenUrl(url: str):
    """
    To open a url in the default browser
    """
    try:
        open_new(url)
    except Exception as e:
        logger.exception(e)
        native_notify("Error", "Cannot open the url specified.")


def get_channel_int(channel_string: str):
    if channel_string.isdigit():
        return int(channel_string)
    elif channel_string.lower() == "mono":
        return 1
    elif channel_string.lower() == "stereo":
        return 2
    else:
        raise ValueError("Invalid channel string")


def native_notify(title: str, message: str):
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
    customMessage: str = "Translation for engine other than Whisper or your local LibreTranslate Deployment "
    "(If you have one) will not work until you reconnect to the internet.",
):
    """
    Notify user that they are not connected to the internet
    """
    native_notify(customTitle, customMessage)


def generate_temp_filename(base_dir):
    """
    Generates a temporary filename with the current date and time.
    """
    return path.join(base_dir, datetime.now().strftime("%Y-%m-%d %H_%M_%S_%f")) + ".wav"


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


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


def emoji_img(size, text):
    font = ImageFont.truetype("seguiemj.ttf", size=int(round(size * 72 / 96, 0)))
    # pixels = points * 96 / 72 : 96 is windowsDPI
    im = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(im)
    draw.text((size / 2, size / 2), text, embedded_color=True, font=font, anchor="mm")
    return ImageTk.PhotoImage(im)


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
            isinstance(widget, tk.Frame) or isinstance(widget, ttk.Frame) or isinstance(widget, tk.LabelFrame)
            or isinstance(widget, ttk.LabelFrame) or isinstance(widget, tk.Label) or isinstance(widget, ttk.Label)
        ):
            # make sure that Button-1 is not already binded
            if "<Button-1>" not in widget.bind():
                widget.bind("<Button-1>", lambda event: root.focus_set())


def windows_os_only(
    widgets: List[Union[
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
    ]]
):
    """
    Disable widgets that are not available on Windows OS

    Args
    ----
        widgets:
            List of widgets to disable
    """
    if system() != "Windows":
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
