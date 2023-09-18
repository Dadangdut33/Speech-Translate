import logging
import os
from time import strftime

from ._path import dir_log

# ------------------ #
current_log: str = f"{strftime('%Y-%m-%d %H-%M-%S')}.log"
# make sure log folder exist
if not os.path.exists(dir_log):
    try:
        os.makedirs(dir_log)
    except Exception as e:
        print("Error: Cannot create log folder")
        print(e)


# ------------------ #
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


init_logging()
