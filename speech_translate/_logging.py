import os
import re
import sys
from time import strftime

from loguru import logger

from ._constants import LOG_FORMAT
from ._path import dir_log

# ------------------ #
FILE_ID = None
recent_stderr = []
current_log: str = f"{strftime('%Y-%m-%d %H-%M-%S')}.log"

# make sure log folder exist
if not os.path.exists(dir_log):
    try:
        os.makedirs(dir_log)
    except Exception as e:
        logger.exception(e)
        logger.error("Error: Cannot create log folder")


def shorten_progress_bar(match):
    percentage = match.group(1)
    percent_bar = "#" * len(percentage)  # make it a bit longer
    return f"{percentage} | {percent_bar} |"


class StreamStderrToLogger(object):
    """
    For stderr and tqdm progress bar
    """
    def __init__(self, level):
        self.level = level
        # tqdm use stderr to print, so we can consider it as info
        self.considered_info = [
            "Downloading", "Fetching", "run_threaded", "Estimating duration from bitrate", "Translating", "Refine", "Align",
            "Running", "done", "Using cache found in", "%|#", "0%|", "model.bin"
        ]

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            line = line.rstrip().replace("\x1B[A", "")

            # checking if line is empty. exception use ^ ~ to point out the error
            # but we don't need it in logger because logger is per line
            check_empty = line.replace("^", "").replace("~", "").strip()
            if len(check_empty) == 0:
                continue

            # check where is it from. if keywords from considered_info is in the line then log as info
            if any(x in line for x in self.considered_info):
                shorten = re.sub(r"(\d+%)(\s*)\|(.+?)\|", shorten_progress_bar, line)
                logger.log("INFO", shorten)
                recent_stderr.append(shorten)

                # limit to max 10
                if len(recent_stderr) > 10:
                    recent_stderr.pop(0)
            else:
                logger.log(self.level, line)

    def flush(self):
        pass


def init_logging(level):
    global FILE_ID
    # add file handler
    FILE_ID = logger.add(
        dir_log + "/" + current_log, level=level, encoding="utf-8", backtrace=False, diagnose=True, format=LOG_FORMAT
    )

    sys.stderr = StreamStderrToLogger("ERROR")
    # tqdm use stderr so we also need to redirect it


def change_log_level(level: str):
    global FILE_ID
    logger.remove(FILE_ID)
    FILE_ID = logger.add(
        dir_log + "/" + current_log, level=level, encoding="utf-8", backtrace=False, diagnose=True, format=LOG_FORMAT
    )


def clear_current_log_file():
    global FILE_ID
    logger.remove(FILE_ID)
    with open(dir_log + "/" + current_log, "w", encoding="utf-8") as f:
        f.write("")
    FILE_ID = logger.add(
        dir_log + "/" + current_log, level="DEBUG", encoding="utf-8", backtrace=False, diagnose=True, format=LOG_FORMAT
    )
