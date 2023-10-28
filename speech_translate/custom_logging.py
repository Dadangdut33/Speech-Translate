import logging
import os
import re
import sys
from time import strftime

from notifypy import Notify, exceptions

from ._constants import APP_NAME
from ._path import dir_log, app_icon, app_icon_missing

# ------------------ #
current_log: str = f"{strftime('%Y-%m-%d %H-%M-%S')}.log"
# make sure log folder exist
if not os.path.exists(dir_log):
    try:
        os.makedirs(dir_log)
    except Exception as e:
        print("Error: Cannot create log folder")
        print(e)


def shorten_progress_bar(match):
    percentage = match.group(1)
    bar = "#" * len(percentage)  # make it a bit longer
    return f"{percentage} | {bar} |"


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.ignore_list = []
        # tqdm use stderr to print, so we should consider it as info
        self.considered_info = ["Downloading", "Fetching", "run_threaded"]

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            line = line.strip().replace("[A", "")

            # ignore if any keywords from ignore_list is in the line
            if any(x in line for x in self.ignore_list):
                continue

            # checking if line is empty. exception use ^ ~ to point out the error
            # but we don't need it in logger because logger is per line
            check_empty = line.replace("^", "").replace("~", "").strip()
            if len(check_empty) == 0:
                continue

            # check where is it from. if keywords from considered_info is in the line then log as info
            if any(x in line for x in self.considered_info):
                self.logger.log(logging.INFO, re.sub(r'(\d+%)(\s*)\|(.+?)\|', shorten_progress_bar, line))
            else:
                self.logger.log(self.level, line)

    def flush(self):
        pass


class StreamFormatter(logging.Formatter):
    bold = "\033[1m"
    green = "\u001b[32;1m"
    white = "\u001b[37m"
    bright_magenta = "\x1b[95m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[34;20m"
    reset = "\x1b[0m"
    timeFormat = blue + "%(asctime)s " + reset
    levelFormat = yellow + "%(levelname)-7s - " + reset
    textFormat = "%(message)s"
    fileLineFormat = green + " (%(filename)s:%(lineno)d) [%(threadName)s]" + reset

    FORMATS = {
        logging.DEBUG: timeFormat + levelFormat + bold + bright_magenta + textFormat + reset + fileLineFormat,
        logging.INFO: timeFormat + levelFormat + white + textFormat + reset + fileLineFormat,
        logging.WARNING: timeFormat + levelFormat + yellow + textFormat + reset + fileLineFormat,
        logging.ERROR: timeFormat + levelFormat + red + textFormat + reset + fileLineFormat,
        logging.CRITICAL: timeFormat + levelFormat + bold_red + textFormat + reset + fileLineFormat,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    textFormat = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d) [%(threadName)s]"

    FORMATS = {
        logging.DEBUG: textFormat,
        logging.INFO: textFormat,
        logging.WARNING: textFormat,
        logging.ERROR: textFormat,
        logging.CRITICAL: textFormat,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# ------------------ #
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


def init_logging():
    global logger
    logger = logging.getLogger(__name__)

    # reset logger
    for handler in logger.handlers[:]:  # make a copy of the list
        logger.removeHandler(handler)

    # Create a custom logger
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(dir_log + "/" + current_log, encoding="utf-8", mode="w")
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_handler.setFormatter(StreamFormatter())
    f_handler.setFormatter(FileFormatter())

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    # logger.addHandler(TqdmLoggingHandler())

    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)
    # tqdm use stderr so we also need to redirect it
    # stderr might be more informative in its original form so you can comment it out if you want when developing


def update_stdout_ignore_list(ignore_list):
    assert isinstance(sys.stdout, StreamToLogger)
    sys.stdout.ignore_list = ignore_list


init_logging()
