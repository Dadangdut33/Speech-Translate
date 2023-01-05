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


def whisper_result_to_srt(result):
    """
    Generate SRT format from Whisper result
    from https://github.com/openai/whisper/discussions/262#discussioncomment-4164515
    """
    text = []
    for i, s in enumerate(result["segments"]):
        text.append(str(i + 1))

        time_start = s["start"]
        hours, minutes, seconds = int(time_start / 3600), (time_start / 60) % 60, (time_start) % 60
        timestamp_start = "%02d:%02d:%06.3f" % (hours, minutes, seconds)
        timestamp_start = timestamp_start.replace(".", ",")
        time_end = s["end"]

        hours, minutes, seconds = int(time_end / 3600), (time_end / 60) % 60, (time_end) % 60
        timestamp_end = "%02d:%02d:%06.3f" % (hours, minutes, seconds)
        timestamp_end = timestamp_end.replace(".", ",")
        text.append(timestamp_start + " --> " + timestamp_end)
        text.append(s["text"].strip() + "\n")

    return "\n".join(text)


def srt_to_txt_format(srt: str):
    """
    Convert SRT format to text format
    """
    text = []
    for line in srt.splitlines():
        if line.strip().isdigit():
            continue
        if "-->" in line:
            continue
        if line.strip() == "":
            continue
        text.append(line.strip())
    return "\n".join(text)


def getFileNameOnlyFromPath(path: str):
    return path.split("/")[-1]
