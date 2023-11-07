import os
import re
import sys
from time import strftime

from loguru import logger
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


def shorten_progress_bar(match):
    percentage = match.group(1)
    bar = "#" * len(percentage)  # make it a bit longer
    return f"{percentage} | {bar} |"


# class StreamStdoutToLogger(object):
#     """
#     Fake file-like stream object that redirects writes to a logger instance.
#     """
#     def __init__(self, level):
#         self.level = level
#         self.ignore_list = []

#     def write(self, buf):
#         for line in buf.rstrip().splitlines():
#             line = line.strip()

#             # ignore if any keywords from ignore_list is in the line
#             if any(x in line for x in self.ignore_list):
#                 continue

#             # checking if line is empty. exception use ^ ~ to point out the error
#             # but we don't need it in logger because logger is per line
#             check_empty = line.replace("^", "").replace("~", "").strip()
#             if len(check_empty) == 0:
#                 continue

#             logger.log(self.level, line)

#     def flush(self):
#         pass

recent_stderr = []


class StreamStderrToLogger(object):
    """
    For stderr and tqdm progress bar
    """
    def __init__(self, level):
        self.level = level
        # tqdm use stderr to print, so we should consider it as info
        self.considered_info = [
            "Downloading", "Fetching", "run_threaded", "Estimating duration from bitrate, this may be inaccurate",
            "Transcribe", "Translate", "Refine", "Align", "Running", "done"
        ]

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            line = line.strip().replace("[A", "")

            # checking if line is empty. exception use ^ ~ to point out the error
            # but we don't need it in logger because logger is per line
            check_empty = line.replace("^", "").replace("~", "").strip()
            if len(check_empty) == 0:
                continue

            # check where is it from. if keywords from considered_info is in the line then log as info
            if any(x in line for x in self.considered_info):
                shorten = re.sub(r'(\d+%)(\s*)\|(.+?)\|', shorten_progress_bar, line)
                logger.log("INFO", shorten)
                recent_stderr.append(shorten)
            else:
                logger.log(self.level, line)
                recent_stderr.append(line)

            # limit to max 10
            if len(recent_stderr) > 10:
                recent_stderr.pop(0)

    def flush(self):
        pass


log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <7}</level> | <cyan>{file}</cyan>:<cyan>{line}</cyan> [{thread.name}] - <level>{message}</level>'
stdout_id = None
file_id = None


def init_logging(level):
    global stdout_id, file_id
    # reset logger
    logger.remove()

    # add handler
    stdout_id = logger.add(sys.stderr, level=level, backtrace=False, diagnose=True, format=log_format)
    file_id = logger.add(
        dir_log + "/" + current_log, level="DEBUG", encoding="utf-8", backtrace=False, diagnose=True, format=log_format
    )

    # sys.stdout = StreamStdoutToLogger("INFO")
    sys.stderr = StreamStderrToLogger("ERROR")
    # tqdm use stderr so we also need to redirect it
    # stderr might be more informative in its original form so you can comment it out if you want when developing


def change_log_level(level: str):
    global current_log, stdout_id, file_id
    logger.remove(stdout_id)
    stdout_id = logger.add(sys.stdout, level=level, backtrace=False, diagnose=True)

    logger.remove(file_id)
    file_id = logger.add(dir_log + "/" + current_log, level=level, encoding="utf-8", backtrace=False, diagnose=True)


# def update_stdout_ignore_list(ignore_list):
#     assert isinstance(sys.stdout, StreamStdoutToLogger)
#     sys.stdout.ignore_list = ignore_list


def clear_current_log_file():
    global current_log, stdout_id, file_id
    logger.remove(file_id)
    with open(dir_log + "/" + current_log, "w") as f:
        f.write("")
    file_id = logger.add(dir_log + "/" + current_log, level="DEBUG", encoding="utf-8", backtrace=False, diagnose=True)
